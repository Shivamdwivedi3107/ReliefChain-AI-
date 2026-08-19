const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("=== Deploying ReliefChainLedger Smart Contract ===");
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contract with account:", deployer.address);

  const ReliefChainLedger = await hre.ethers.getContractFactory("ReliefChainLedger");
  const ledger = await ReliefChainLedger.deploy();
  await ledger.waitForDeployment();

  const contractAddress = await ledger.getAddress();
  console.log("ReliefChainLedger deployed to:", contractAddress);

  // Save contract artifact and address for backend Web3 integration
  const deploymentData = {
    contractAddress: contractAddress,
    deployerAddress: deployer.address,
    network: hre.network.name,
    deployedAt: new Date().toISOString(),
  };

  const artifactPath = path.join(__dirname, "../contract_address.json");
  fs.writeFileSync(artifactPath, JSON.stringify(deploymentData, null, 2));
  console.log("Contract metadata written to:", artifactPath);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
