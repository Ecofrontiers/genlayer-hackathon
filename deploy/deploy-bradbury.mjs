/**
 * Deploy GridOracle + SpatialRouterSimple to GenLayer Bradbury Testnet.
 * Requires funded deployer account.
 *
 * Usage: DEPLOYER_KEY=0x... node deploy/deploy-bradbury.mjs
 */

import { createClient, createAccount } from 'genlayer-js';
import { testnetBradbury } from 'genlayer-js/chains';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');

const DEPLOYER_KEY = process.env.DEPLOYER_KEY;
if (!DEPLOYER_KEY) {
  console.error('Set DEPLOYER_KEY env var. Example:');
  console.error('  DEPLOYER_KEY=0xabc... node deploy/deploy-bradbury.mjs');
  process.exit(1);
}

const account = createAccount(DEPLOYER_KEY);
const client = createClient({ chain: testnetBradbury, account });

console.log('Network:  Bradbury Testnet');
console.log('Deployer:', account.address);
console.log('RPC:     ', testnetBradbury.rpcUrls.default.http[0]);
console.log('Explorer: https://explorer-bradbury.genlayer.com');
console.log('');

async function deployContract(name, filePath) {
  console.log(`Deploying ${name}...`);
  const code = readFileSync(filePath, 'utf-8');

  const txHash = await client.deployContract({
    code: new TextEncoder().encode(code),
    args: [],
  });
  console.log(`  tx: ${txHash}`);
  console.log(`  explorer: https://explorer-bradbury.genlayer.com/txs/${txHash}`);

  const receipt = await client.waitForTransactionReceipt({
    hash: txHash,
    retries: 120,
    interval: 5000,
  });

  const addr = receipt.data?.contract_address
    || receipt.txDataDecoded?.contractAddress
    || receipt.contractAddress;

  console.log(`  ${name} deployed at: ${addr}`);
  return addr;
}

async function callWrite(addr, fn, args, label) {
  console.log(`  ${label}...`);
  const tx = await client.writeContract({
    address: addr, functionName: fn, args, value: BigInt(0),
  });
  await client.waitForTransactionReceipt({ hash: tx, retries: 60, interval: 5000 });
  console.log(`    done (${tx.slice(0, 10)}...)`);
}

async function main() {
  // Step 1: Deploy GridOracle (or reuse existing)
  const EXISTING_ORACLE = process.env.ORACLE_ADDR || '';
  const oracleAddr = EXISTING_ORACLE || await deployContract('GridOracle', resolve(root, 'contracts/grid_oracle.py'));
  if (EXISTING_ORACLE) console.log(`Reusing GridOracle: ${EXISTING_ORACLE}`);

  // Step 2: Seed zone data
  console.log('\nSeeding zones...');
  const zones = [
    ['FI', 45, 82],
    ['DE', 302, 55],
    ['US', 420, 22],
  ];
  for (const [zone, carbon, renewable] of zones) {
    await callWrite(oracleAddr, 'update_zone_hardcoded', [zone, carbon, renewable], `Seed ${zone}`);
  }

  // Step 4: Verify
  const data = await client.readContract({ address: oracleAddr, functionName: 'get_zone_data', args: [] });
  console.log('  Zone data:', data);

  // Step 5: Deploy SpatialRouterSimple
  const routerAddr = await deployContract('SpatialRouterSimple', resolve(root, 'contracts/spatial_router_simple.py'));

  // Step 6: Test routing
  console.log('\nTest routing...');
  const tx = await client.writeContract({
    address: routerAddr, functionName: 'route_simple', args: ['greenest possible'], value: BigInt(0),
  });
  console.log(`  tx: ${tx}`);
  console.log(`  explorer: https://explorer-bradbury.genlayer.com/txs/${tx}`);

  const receipt = await client.waitForTransactionReceipt({ hash: tx, retries: 120, interval: 5000 });
  console.log('  Result:', JSON.stringify(receipt.data || receipt.result, null, 2));

  // Summary
  console.log('\n═══════════════════════════════════════════════════');
  console.log('BRADBURY DEPLOYMENT COMPLETE');
  console.log('═══════════════════════════════════════════════════');
  console.log(`GridOracle:          ${oracleAddr}`);
  console.log(`SpatialRouterSimple: ${routerAddr}`);
  console.log('');
  console.log('Explorer links:');
  console.log(`  Oracle:  https://explorer-bradbury.genlayer.com/address/${oracleAddr}`);
  console.log(`  Router:  https://explorer-bradbury.genlayer.com/address/${routerAddr}`);
  console.log('');
  console.log('Update frontend config:');
  console.log(`  GRID_ORACLE_ADDR = '${oracleAddr}'`);
  console.log(`  SPATIAL_ROUTER_ADDR = '${routerAddr}'`);
  console.log('═══════════════════════════════════════════════════');
}

main().catch(e => { console.error('Deploy failed:', e); process.exit(1); });
