import * as duckdb from '@duckdb/duckdb-wasm';

const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();

let dbPromise: Promise<duckdb.AsyncDuckDB> | null = null;

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

  URL.revokeObjectURL(workerUrl);
  return db;
}

export async function getDb(): Promise<duckdb.AsyncDuckDB> {
  if (!dbPromise) {
    dbPromise = createDb();
  }
  return dbPromise;
}

export async function executeQuery(sql: string): Promise<{ columns: string[], rows: any[] }> {
  const db = await getDb();
  const conn = await db.connect();
  
  try {
    const result = await conn.query(sql);
    
    // Get column names
    const columns = result.schema.fields.map((field: any) => field.name);
    
    // Convert result to rows
    const rows: any[] = [];
    for await (const row of result) {
      const rowData: any = {};
      columns.forEach((col, index) => {
        rowData[col] = row[index];
      });
      rows.push(rowData);
    }
    
    return { columns, rows };
  } finally {
    await conn.close();
  }
}
