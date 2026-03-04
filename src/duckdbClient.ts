import * as duckdb from '@duckdb/duckdb-wasm';

const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();

let dbPromise: Promise<duckdb.AsyncDuckDB> | null = null;
let dbInstance: duckdb.AsyncDuckDB | null = null;

async function createDb(): Promise<duckdb.AsyncDuckDB> {
  // Select an appropriate bundle for this browser.
  const bundle = await duckdb.selectBundle(JSDELIVR_BUNDLES);

  if (!bundle.mainWorker || !bundle.mainModule) {
    throw new Error('Failed to select a DuckDB-WASM bundle for this browser.');
  }

  // Construct a same-origin worker that bootstraps the remote worker script.
  const workerUrl = URL.createObjectURL(
    new Blob([`importScripts("${bundle.mainWorker}");`], {
      type: 'text/javascript'
    })
  );

  const worker = new Worker(workerUrl);
  const logger = new duckdb.ConsoleLogger();
  const db = new duckdb.AsyncDuckDB(logger, worker);

  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
  
  // Use in-memory database (default behavior)
  // This ensures all connections share the same database instance
  
  URL.revokeObjectURL(workerUrl);
  dbInstance = db;
  return db;
}

export async function getDb(): Promise<duckdb.AsyncDuckDB> {
  if (!dbPromise) {
    dbPromise = createDb();
  }
  return dbPromise;
}

export async function executeQuery(sql: string): Promise<{ columns: string[], rows: any[] }> {
  console.log('Executing query:', sql);
  const db = await getDb();
  const conn = await db.connect();
  
  try {
    // Show available tables for debugging
    try {
      const tablesResult = await conn.query("SHOW TABLES");
      console.log('Available tables result:', tablesResult);
      
      const tables: string[] = [];
      for (const row of tablesResult) {
        // DuckDB SHOW TABLES returns table names in 'name' column
        const tableName = row.name || row.table_name || Object.values(row)[0];
        if (tableName) {
          tables.push(tableName);
        }
      }
      console.log('Available tables:', tables);
    } catch (e) {
      console.log('Error showing tables:', e);
    }
    
    const result = await conn.query(sql);
    console.log('Query result type:', typeof result);
    console.log('Query result:', result);
    
    // Get column names
    const columns = result.schema.fields.map((field: any) => field.name);
    console.log('Columns:', columns);
    
    // Convert result to rows - use same pattern as EXPLAIN functionality
    const rows: any[] = [];
    for (const row of result) {
      const rowData: any = {};
      columns.forEach((col, index) => {
        // Try different ways to access row data
        rowData[col] = row[col] || row[index] || Object.values(row)[index];
      });
      rows.push(rowData);
    }
    
    console.log('Total rows:', rows.length);
    if (rows.length > 0) {
      console.log('First row:', rows[0]);
    }
    
    return { columns, rows };
  } catch (error) {
    console.error('Query execution error:', error);
    throw error;
  } finally {
    await conn.close();
  }
}
