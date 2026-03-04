import React, { useEffect, useMemo, useState } from 'react';
import { getDb, executeQuery } from './duckdbClient';

type SchemaRow = {
  column_name: string;
  data_type: string;
};

type ExplainRow = {
  explain_value: string;
};

// Helper function to create a simple diff between original and optimized SQL
const createSqlDiff = (original: string, optimized: string): JSX.Element[] => {
  const originalLines = original.trim().split('\n');
  const optimizedLines = optimized.trim().split('\n');
  
  const diff: JSX.Element[] = [];
  const maxLines = Math.max(originalLines.length, optimizedLines.length);
  
  for (let i = 0; i < maxLines; i++) {
    const originalLine = originalLines[i] || '';
    const optimizedLine = optimizedLines[i] || '';
    
    if (originalLine === optimizedLine) {
      diff.push(<div key={i} className="diff-unchanged">{optimizedLine}</div>);
    } else if (originalLine && !optimizedLine) {
      diff.push(<div key={i} className="diff-removed">- {originalLine}</div>);
    } else if (!originalLine && optimizedLine) {
      diff.push(<div key={i} className="diff-added">+ {optimizedLine}</div>);
    } else {
      diff.push(<div key={i} className="diff-removed">- {originalLine}</div>);
      diff.push(<div key={i + 1000} className="diff-added">+ {optimizedLine}</div>);
    }
  }
  
  return diff;
};

// Helper function to download query plan
const downloadQueryPlan = (plan: string[]) => {
  const content = plan.join('\n');
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `query-plan-${new Date().toISOString().slice(0, 10)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

type DatasetInfo = {
  name: string;
  tableName: string;
  schema: SchemaRow[];
};

type AgentResult = {
  status: string;
  execution_time_ms: number;
  [key: string]: any;
};

type PipelinePerformance = {
  total_time_ms: number;
  agents_completed: number;
};

type OptimizationResult = {
  optimized_sql: string;
  explanation: string;
  agent_results: {
    analyzer: AgentResult;
    optimizer: AgentResult;
    validator: AgentResult;
    explainer: AgentResult;
  };
  pipeline_performance: PipelinePerformance;
};

export const App: React.FC = () => {
  const [dbReady, setDbReady] = useState(false);
  const [loadingDb, setLoadingDb] = useState(true);
  const [dbError, setDbError] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [schemaError, setSchemaError] = useState<string | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [sql, setSql] = useState('');
  const [plan, setPlan] = useState<string[]>([]);
  const [planError, setPlanError] = useState<string | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [optLoading, setOptLoading] = useState(false);
  const [optError, setOptError] = useState<string | null>(null);
  const [optimizedSql, setOptimizedSql] = useState('');
  const [optExplanation, setOptExplanation] = useState('');
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [queryResults, setQueryResults] = useState<{ columns: string[], rows: any[] } | null>(null);
  const [queryResultsError, setQueryResultsError] = useState<string | null>(null);
  const [queryResultsLoading, setQueryResultsLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setLoadingDb(true);
        await getDb();
        setDbReady(true);
      } catch (e) {
        setDbError((e as Error).message ?? 'Failed to initialise DuckDB');
      } finally {
        setLoadingDb(false);
      }
    })();
  }, []);

  const allSchemas = useMemo(() => {
    return datasets.flatMap(dataset => 
      dataset.schema.map(row => ({ ...row, table_name: dataset.tableName }))
    );
  }, [datasets]);

  const schemaTable = useMemo(
    () =>
      allSchemas.length ? (
        <div>
          {datasets.map((dataset) => (
            <div key={dataset.tableName} style={{ marginBottom: '16px' }}>
              <div className="pill pill-outline" style={{ marginBottom: '8px' }}>
                Table: {dataset.name} ({dataset.tableName})
              </div>
              <table className="schema-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Column</th>
                    <th>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {dataset.schema.map((row, idx) => (
                    <tr key={row.column_name}>
                      <td>{idx + 1}</td>
                      <td>{row.column_name}</td>
                      <td>{row.data_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      ) : (
        <div className="panel-empty">Upload up to 3 datasets to see their schemas.</div>
      ),
    [datasets]
  );

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    if (datasets.length >= 3) {
      setSchemaError('Maximum 3 datasets allowed');
      return;
    }

    setSchemaError(null);
    setPlan([]);
    setPlanError(null);

    try {
      setSchemaLoading(true);
      const buffer = await file.arrayBuffer();
      const db = await getDb();

      const conn = await db.connect();
      const virtualFileName = `upload_${Date.now()}.csv`;

      await db.registerFileBuffer(virtualFileName, new Uint8Array(buffer));

      const safeTableName = `t_${Date.now().toString(36)}`;
      await conn.query(
        `CREATE OR REPLACE TABLE ${safeTableName} AS SELECT * FROM read_csv_auto('${virtualFileName}', HEADER=TRUE);`
      );

      const result = await conn.query<any>(
        `SELECT name AS column_name,
                type AS data_type
         FROM pragma_table_info('${safeTableName}')
         ORDER BY cid;`
      );

      const rows: SchemaRow[] = [];
      for (const row of result) {
        const r = row as any;
        rows.push({
          column_name: r.column_name,
          data_type: r.data_type
        });
      }

      const datasetName = file.name.replace(/\.[^/.]+$/, '');
      const newDataset: DatasetInfo = {
        name: datasetName,
        tableName: safeTableName,
        schema: rows
      };

      setDatasets(prev => [...prev, newDataset]);
      if (!sql) {
        setSql(`SELECT * FROM ${safeTableName} LIMIT 10;`);
      }
      await conn.close();
    } catch (e) {
      setSchemaError((e as Error).message ?? 'Failed to load dataset');
    } finally {
      setSchemaLoading(false);
      event.target.value = '';
    }
  }

  async function handleExplain() {
    if (!sql.trim()) {
      setPlanError('Write a SQL query first.');
      return;
    }
    try {
      setPlanLoading(true);
      setPlanError(null);
      setPlan([]);

      const db = await getDb();
      const conn = await db.connect();
      const explainSql = `EXPLAIN ${sql}`;
      const result = await conn.query<ExplainRow[]>(explainSql);

      const lines: string[] = [];
      for (const row of result) {
        // @ts-expect-error duckdb-wasm row typing
        const value = (row as any).explain_value ?? Object.values(row as any)[0];
        if (typeof value === 'string') {
          lines.push(value);
        }
      }

      setPlan(lines.length ? lines : ['(no plan output)']);
      await conn.close();
    } catch (e) {
      setPlanError((e as Error).message ?? 'Failed to run EXPLAIN');
    } finally {
      setPlanLoading(false);
    }
  }

  async function handleOptimize() {
    if (!sql.trim()) {
      setOptError('Write a SQL query first.');
      return;
    }

    try {
      setOptLoading(true);
      setOptError(null);
      setOptimizedSql('');
      setOptExplanation('');
      setOptimizationResult(null);

      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => {
        controller.abort();
      }, 180000); // Increased timeout for multi-agent processing

      const apiUrl = process.env.REACT_APP_API_URL || '/api/optimize-sql';
      console.log('Calling API at:', apiUrl);
      
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ sql, schema: allSchemas }),
        signal: controller.signal
      });

      window.clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`Multi-agent optimizer returned ${res.status}`);
      }

      const data = await res.json() as OptimizationResult;

      setOptimizedSql(data.optimized_sql ?? '');
      setOptExplanation(data.explanation ?? '');
      setOptimizationResult(data);

      // Execute the optimized query to show results
      if (data.optimized_sql && data.optimized_sql !== null) {
        try {
          setQueryResultsLoading(true);
          setQueryResultsError(null);
          const results = await executeQuery(data.optimized_sql);
          setQueryResults(results);
        } catch (e) {
          setQueryResultsError((e as Error).message ?? 'Failed to execute optimized query');
          setQueryResults(null);
        } finally {
          setQueryResultsLoading(false);
        }
      } else {
        // No optimization, execute original query
        try {
          setQueryResultsLoading(true);
          setQueryResultsError(null);
          const results = await executeQuery(sql);
          setQueryResults(results);
        } catch (e) {
          setQueryResultsError((e as Error).message ?? 'Failed to execute query');
          setQueryResults(null);
        } finally {
          setQueryResultsLoading(false);
        }
      }
    } catch (e) {
      if ((e as Error).name === 'AbortError') {
        setOptError('Timed out waiting for optimizer. The model may still be loading.');
      } else {
        setOptError((e as Error).message ?? 'Failed to optimize SQL');
      }
    } finally {
      setOptLoading(false);
    }
  }

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="logo-mark" />
        <div className="logo-text">
          <span className="logo-primary">🧠 Multi-Agent SQL Optimizer</span>
          <span className="logo-secondary">Advanced database optimization with 4 specialized AI agents</span>
        </div>
        <div className="header-status">
          {loadingDb && <span className="pill pill-muted">Booting DuckDB…</span>}
          {!loadingDb && dbReady && <span className="pill pill-ok">DuckDB ready</span>}
          {dbError && <span className="pill pill-error">DuckDB error</span>}
        </div>
      </header>

      <main className="layout">
        <section className="left-column">
          <div className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Dataset</h2>
                <p className="panel-subtitle">
                  Upload a CSV file to explore its schema and query plan.
                </p>
              </div>
              <label className="upload-button">
                <input
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleFileUpload}
                  disabled={schemaLoading}
                />
                <span>{schemaLoading ? 'Loading…' : 'Upload CSV'}</span>
              </label>
            </div>
            <div className="panel-body scrollable">
              {dbError && <div className="alert alert-error">DuckDB error: {dbError}</div>}
              {schemaError && <div className="alert alert-error">{schemaError}</div>}
              {datasets.length > 0 && (
                <div className="badge-row">
                  {datasets.map((dataset, idx) => (
                    <div key={idx} className="badge">
                      Table: {dataset.name} ({dataset.tableName})
                    </div>
                  ))}
                </div>
              )}
              {schemaTable}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">SQL query</h2>
                <p className="panel-subtitle">
                  Type any DuckDB SQL and we&apos;ll show you the query plan.
                </p>
              </div>
              <div className="header-actions">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={handleExplain}
                  disabled={planLoading || !sql.trim()}
                >
                  {planLoading ? '🔄 Explaining…' : '📋 Explain Query'}
                </button>
                <button
                  className="primary-button"
                  type="button"
                  onClick={handleOptimize}
                  disabled={optLoading || !sql.trim()}
                >
                  {optLoading ? '🤖 Running Agents…' : '🧠 Multi-Agent Optimize'}
                </button>
              </div>
            </div>
            <div className="panel-body">
              {!datasets.length && (
                <div className="panel-empty">Upload datasets first to enable planning.</div>
              )}
              <textarea
                className="sql-editor"
                spellCheck={false}
                placeholder={
                  datasets.length > 0
                    ? `e.g. SELECT * FROM ${datasets[0].tableName} WHERE ...`
                    : 'Upload datasets to start writing SQL…'
                }
                value={sql}
                onChange={(e) => setSql(e.target.value)}
                disabled={!dbReady || !datasets.length}
              />
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Model suggestions</h2>
              </div>
            </div>
            <div className="panel-body scrollable">
              {optError && <div className="alert alert-error">{optError}</div>}
              {!optimizedSql && !optExplanation && !optError && (
                <div className="panel-empty">
                  Click &ldquo;Optimise SQL&rdquo; to run the multi-agent optimization pipeline.
                  <div style={{ marginTop: '12px', fontSize: '11px', color: '#aaaab5' }}>
                    🤖 4 specialized AI agents will analyze your query
                  </div>
                </div>
              )}
              
              {optimizationResult && (
                <>
                  <div className="pill pill-outline">🧠 Multi-Agent Pipeline Results</div>
                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ fontSize: '11px', color: '#b5b5c0', marginBottom: '8px' }}>
                      Pipeline completed in {optimizationResult.pipeline_performance.total_time_ms.toFixed(1)}ms
                    </div>
                    
                    {/* Agent Status */}
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ fontSize: '11px', fontWeight: '600', marginBottom: '6px', color: '#f5f5f8' }}>
                        Agent Execution Status:
                      </div>
                      <div style={{ display: 'grid', gap: '4px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                          <span>🔹 Agent 1 - Query Analyzer</span>
                          <span style={{ color: optimizationResult.agent_results.analyzer.status === 'completed' ? '#90ee90' : '#ff6b6b' }}>
                            {optimizationResult.agent_results.analyzer.status} ({optimizationResult.agent_results.analyzer.execution_time_ms.toFixed(1)}ms)
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                          <span>🔹 Agent 2 - Optimizer Generator</span>
                          <span style={{ color: optimizationResult.agent_results.optimizer.status === 'completed' ? '#90ee90' : '#ff6b6b' }}>
                            {optimizationResult.agent_results.optimizer.status} ({optimizationResult.agent_results.optimizer.execution_time_ms.toFixed(1)}ms)
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                          <span>🔹 Agent 3 - Validator</span>
                          <span style={{ color: optimizationResult.agent_results.validator.status === 'completed' ? '#90ee90' : '#ff6b6b' }}>
                            {optimizationResult.agent_results.validator.status} ({optimizationResult.agent_results.validator.execution_time_ms.toFixed(1)}ms)
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                          <span>🔹 Agent 4 - Explainer</span>
                          <span style={{ color: optimizationResult.agent_results.explainer.status === 'completed' ? '#90ee90' : '#ff6b6b' }}>
                            {optimizationResult.agent_results.explainer.status} ({optimizationResult.agent_results.explainer.execution_time_ms.toFixed(1)}ms)
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Pipeline Stats */}
                    <div style={{ marginBottom: '12px', padding: '8px', background: '#020204', borderRadius: '6px', border: '1px solid #25252e' }}>
                      <div style={{ fontSize: '10px', color: '#b5b5c0' }}>
                        • Candidates Generated: {optimizationResult.agent_results.optimizer.candidates_generated || 0}
                      </div>
                      <div style={{ fontSize: '10px', color: '#b5b5c0' }}>
                        • Candidates Validated: {optimizationResult.agent_results.validator.candidates_validated || 0}
                      </div>
                      <div style={{ fontSize: '10px', color: '#b5b5c0' }}>
                        • Agents Completed: {optimizationResult.pipeline_performance.agents_completed}/4
                      </div>
                    </div>
                  </div>
                </>
              )}
              
              {optimizedSql && (
                <>
                  <div className="pill pill-outline">Optimised SQL</div>
                  <div className="sql-diff">
                    {createSqlDiff(sql, optimizedSql.replace(/`/g, ''))}
                  </div>
                </>
              )}
              {optExplanation && (
                <>
                  <div className="pill pill-outline">What changed and why</div>
                  <div className="explanation-text">{optExplanation}</div>
                </>
              )}
              
              {optimizationResult && (
                <>
                  <div style={{ marginBottom: '24px' }}></div>
                  <div className="pill pill-outline">📊 Query Results</div>
                  
                  {queryResultsLoading && (
                    <div style={{ marginBottom: '16px', padding: '12px', background: '#020204', borderRadius: '8px', border: '1px solid #25252e' }}>
                      <div style={{ fontSize: '11px', color: '#b5b5c0' }}>🔄 Executing query...</div>
                    </div>
                  )}
                  
                  {queryResultsError && (
                    <div style={{ marginBottom: '16px', padding: '12px', background: '#020204', borderRadius: '8px', border: '1px solid #25252e' }}>
                      <div style={{ fontSize: '11px', color: '#ff6b6b' }}>❌ {queryResultsError}</div>
                    </div>
                  )}
                  
                  {queryResults && (
                    <div style={{ marginBottom: '16px', background: '#020204', borderRadius: '8px', border: '1px solid #25252e' }}>
                      <div style={{ padding: '12px', borderBottom: '1px solid #25252e' }}>
                        <div style={{ fontSize: '11px', fontWeight: '600', color: '#f5f5f8' }}>
                          Query Results ({queryResults.rows.length} rows)
                        </div>
                      </div>
                      
                      <div style={{ overflowX: 'auto', maxHeight: '300px', overflowY: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                          <thead style={{ position: 'sticky', top: 0, background: '#1a1a1e', zIndex: 1 }}>
                            <tr>
                              {queryResults.columns.map((col, idx) => (
                                <th key={idx} style={{ 
                                  padding: '8px 12px', 
                                  textAlign: 'left', 
                                  borderBottom: '1px solid #25252e',
                                  color: '#f5f5f8',
                                  fontWeight: '600',
                                  fontSize: '10px'
                                }}>
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {queryResults.rows.map((row, rowIdx) => (
                              <tr key={rowIdx} style={{ 
                                borderBottom: rowIdx < queryResults.rows.length - 1 ? '1px solid #25252e' : 'none'
                              }}>
                                {queryResults.columns.map((col, colIdx) => (
                                  <td key={colIdx} style={{ 
                                    padding: '8px 12px', 
                                    color: '#e5e5ee',
                                    fontSize: '10px'
                                  }}>
                                    {row[col]?.toString() ?? ''}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </section>

        <section className="right-column">
          <div className="panel plan-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Query plan</h2>
                <p className="panel-subtitle">
                  DuckDB physical plan for your SQL, updated on demand.
                </p>
              </div>
              <button
                className="download-button"
                type="button"
                onClick={() => downloadQueryPlan(plan)}
                disabled={!plan.length}
              >
                Download Plan
              </button>
            </div>
            <div className="panel-body scrollable">
              {planError && <div className="alert alert-error">{planError}</div>}
              {!plan.length && !planError && (
                <div className="panel-empty">Hit &ldquo;Run EXPLAIN&rdquo; to see the plan.</div>
              )}
              {!!plan.length && (
                <pre className="plan-view">
                  {plan.map((line, idx) => (
                    <div key={idx} className="plan-line">
                      <span className="plan-gutter">{idx + 1}</span>
                      <span className="plan-text">{line}</span>
                    </div>
                  ))}
                </pre>
              )}
            </div>
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <span>DuckDB runs fully in your browser. No data leaves this page.</span>
      </footer>
    </div>
  );
};

