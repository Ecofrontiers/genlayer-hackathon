/**
 * Deploy GridOracle and SpatialRouter to GenLayer.
 *
 * Usage:
 *   genlayer network testnet-bradbury  # or localnet for dev
 *   genlayer deploy
 *
 * This script is auto-discovered by `genlayer deploy` (sorts by filename).
 * It deploys GridOracle first, then SpatialRouter with the oracle address.
 */
import { readFileSync } from "fs";
import path from "path";

export default async function main(client) {
  // Step 1: Deploy GridOracle
  console.log("Deploying GridOracle...");
  const oracleCode = new Uint8Array(
    readFileSync(path.resolve(process.cwd(), "contracts/grid_oracle.py"))
  );
  const oracleTx = await client.deployContract({ code: oracleCode, args: [] });
  const oracleReceipt = await client.waitForTransactionReceipt({
    hash: oracleTx,
    retries: 200,
  });
  const oracleAddr = oracleReceipt.data?.contract_address
    || oracleReceipt.txDataDecoded?.contractAddress;
  console.log(`GridOracle deployed at: ${oracleAddr}`);

  // Step 2: Seed GridOracle with initial data (hardcoded fallback)
  console.log("Seeding GridOracle with initial zone data...");
  await client.writeContract({
    address: oracleAddr,
    functionName: "update_zone_hardcoded",
    args: ["GB", 263, 40],
    value: BigInt(0),
  });
  await client.writeContract({
    address: oracleAddr,
    functionName: "update_zone_hardcoded",
    args: ["FI", 45, 82],
    value: BigInt(0),
  });
  await client.writeContract({
    address: oracleAddr,
    functionName: "update_zone_hardcoded",
    args: ["DE", 302, 55],
    value: BigInt(0),
  });
  console.log("GridOracle seeded with GB=263, FI=45, DE=302 gCO2/kWh");

  // Step 3: Deploy SpatialRouter with GridOracle address
  console.log("Deploying SpatialRouter...");
  const routerCode = new Uint8Array(
    readFileSync(path.resolve(process.cwd(), "contracts/spatial_router.py"))
  );
  const routerTx = await client.deployContract({
    code: routerCode,
    args: [oracleAddr],
  });
  const routerReceipt = await client.waitForTransactionReceipt({
    hash: routerTx,
    retries: 200,
  });
  const routerAddr = routerReceipt.data?.contract_address
    || routerReceipt.txDataDecoded?.contractAddress;
  console.log(`SpatialRouter deployed at: ${routerAddr}`);

  // Step 4: Print summary
  console.log("\n=== DEPLOYMENT COMPLETE ===");
  console.log(`GridOracle:    ${oracleAddr}`);
  console.log(`SpatialRouter: ${routerAddr}`);
  console.log("\nUpdate frontend/index.html with these addresses:");
  console.log(`  GRID_ORACLE_ADDR = '${oracleAddr}';`);
  console.log(`  SPATIAL_ROUTER_ADDR = '${routerAddr}';`);

  return { oracleAddr, routerAddr };
}
