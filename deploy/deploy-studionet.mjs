/**
 * Deploy GridOracle + SpatialRouter to GenLayer Studionet.
 * No Docker needed — uses hosted studio.genlayer.com/api.
 *
 * Usage: node deploy/deploy-studionet.mjs
 */

import { createClient, createAccount, generatePrivateKey } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');

// Create a fresh account for deployment
const account = createAccount(generatePrivateKey());
const client = createClient({ chain: studionet, account });

console.log('Deployer address:', account.address);
console.log('Connected to:', studionet.rpcUrls.default.http[0]);
console.log('');

async function deployContract(name, filePath, args = []) {
  console.log(`Deploying ${name}...`);
  const code = readFileSync(filePath, 'utf-8');

  try {
    const txHash = await client.deployContract({
      code: new TextEncoder().encode(code),
      args,
    });
    console.log(`  tx: ${txHash}`);

    const receipt = await client.waitForTransactionReceipt({
      hash: txHash,
      retries: 60,
      interval: 5000,
    });

    const addr = receipt.data?.contract_address
      || receipt.txDataDecoded?.contractAddress
      || receipt.contractAddress;

    console.log(`  ${name} deployed at: ${addr}`);
    return addr;
  } catch (e) {
    console.error(`  FAILED: ${e.message}`);
    throw e;
  }
}

async function seedOracle(oracleAddr) {
  console.log('\nSeeding GridOracle with zone data...');
  const zones = [
    ['GB', 263, 40],
    ['FI', 45, 82],
    ['DE', 302, 55],
  ];

  for (const [zone, carbon, renewable] of zones) {
    try {
      const tx = await client.writeContract({
        address: oracleAddr,
        functionName: 'update_zone_hardcoded',
        args: [zone, carbon, renewable],
        value: BigInt(0),
      });
      await client.waitForTransactionReceipt({ hash: tx, retries: 30, interval: 3000 });
      console.log(`  Seeded ${zone}: ${carbon} gCO2, ${renewable}% renewable`);
    } catch (e) {
      console.error(`  Failed to seed ${zone}: ${e.message}`);
    }
  }
}

async function testRouter(routerAddr) {
  console.log('\nTesting SpatialRouter...');
  try {
    const tx = await client.writeContract({
      address: routerAddr,
      functionName: 'route_inference',
      args: ['What is 2+2?', 'greenest possible'],
      value: BigInt(0),
    });
    console.log(`  route_inference tx: ${tx}`);

    const receipt = await client.waitForTransactionReceipt({
      hash: tx,
      retries: 60,
      interval: 5000,
    });
    console.log('  Result:', JSON.stringify(receipt.data || receipt.result, null, 2));
  } catch (e) {
    console.error(`  Test failed: ${e.message}`);
  }
}

async function readOracle(oracleAddr) {
  console.log('\nReading GridOracle zone data...');
  try {
    const data = await client.readContract({
      address: oracleAddr,
      functionName: 'get_zone_data',
      args: [],
    });
    console.log('  Zone data:', data);
  } catch (e) {
    console.error(`  Read failed: ${e.message}`);
  }
}

// ─── Main ───────────────────────────────────────────────────────────────

async function main() {
  // Step 1: Deploy GridOracle
  const oracleAddr = await deployContract(
    'GridOracle',
    resolve(root, 'contracts/grid_oracle.py')
  );

  // Step 2: Seed zone data
  await seedOracle(oracleAddr);

  // Step 3: Verify oracle data
  await readOracle(oracleAddr);

  // Step 4: Deploy SpatialRouter with oracle address
  const routerAddr = await deployContract(
    'SpatialRouter',
    resolve(root, 'contracts/spatial_router.py'),
    [oracleAddr]
  );

  // Step 5: Test routing
  await testRouter(routerAddr);

  // Summary
  console.log('\n═══════════════════════════════════════');
  console.log('DEPLOYMENT COMPLETE');
  console.log('═══════════════════════════════════════');
  console.log(`GridOracle:    ${oracleAddr}`);
  console.log(`SpatialRouter: ${routerAddr}`);
  console.log('');
  console.log('Update frontend/index.html:');
  console.log(`  const GRID_ORACLE_ADDR = '${oracleAddr}';`);
  console.log(`  const SPATIAL_ROUTER_ADDR = '${routerAddr}';`);
  console.log('═══════════════════════════════════════');
}

main().catch(e => {
  console.error('Deploy failed:', e);
  process.exit(1);
});
