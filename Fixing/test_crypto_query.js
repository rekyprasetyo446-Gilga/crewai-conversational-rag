const { BigQuery } = require('@google-cloud/bigquery');

// Ensure you have authenticated using 'gcloud auth application-default login'
// or set the GOOGLE_APPLICATION_CREDENTIALS environment variable to your Service Account JSON.
const bigquery = new BigQuery();

async function queryCrypto() {
  console.log("🚀 Initializing BigQuery Crypto Search...");
  
  // A query to find the top 5 largest Bitcoin transactions by value
  // pulling directly from Google's public crypto dataset.
  const query = `
    SELECT 
        hash as transaction_hash,
        output_value as total_satoshi,
        (output_value / 100000000) as total_bitcoin,
        block_timestamp
    FROM 
        \`bigquery-public-data.crypto_bitcoin.transactions\`
    WHERE 
        output_value > 0
    ORDER BY 
        output_value DESC
    LIMIT 5;
  `;

  const options = {
    query: query,
    // Location must match that of the dataset(s) referenced in the query.
    location: 'US',
  };

  try {
    // Run the query as a job
    const [job] = await bigquery.createQueryJob(options);
    console.log(`Job ${job.id} started. Querying the public ledger...`);

    // Wait for the query to finish
    const [rows] = await job.getQueryResults();

    console.log("\n💰 Top 5 Largest Bitcoin Transactions Found:\n");
    rows.forEach(row => {
      console.log(`Hash: ${row.transaction_hash}`);
      console.log(`Bitcoin Transferred: ₿${row.total_bitcoin.toLocaleString()}`);
      console.log(`Date: ${row.block_timestamp.value}`);
      console.log('----------------------------------------');
    });
  } catch (error) {
    console.error("❌ BigQuery Error:", error.message);
    console.log("\n[!] Note: You must link your real Google Cloud Credentials (Service Account Key) to run this!");
  }
}

queryCrypto();
