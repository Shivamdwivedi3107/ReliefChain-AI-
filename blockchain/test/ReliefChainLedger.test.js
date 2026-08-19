const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ReliefChainLedger Contract", function () {
  let ReliefChainLedger;
  let ledger;
  let owner;
  let ngoAccount;
  let unauthorizedAccount;

  const mockHash1 = ethers.keccak256(ethers.toUtf8Bytes("donation_event_payload_1"));
  const mockHash2 = ethers.keccak256(ethers.toUtf8Bytes("distribution_payload_2"));

  beforeEach(async function () {
    [owner, ngoAccount, unauthorizedAccount] = await ethers.getSigners();
    ReliefChainLedger = await ethers.getContractFactory("ReliefChainLedger");
    ledger = await ReliefChainLedger.deploy();
    await ledger.waitForDeployment();
  });

  it("Should set the deployer as owner and authorize deployer", async function () {
    expect(await ledger.owner()).to.equal(owner.address);
    expect(await ledger.authorizedCallers(owner.address)).to.equal(true);
  });

  it("Should allow owner to authorize an NGO address", async function () {
    await ledger.setCallerAuthorization(ngoAccount.address, true);
    expect(await ledger.authorizedCallers(ngoAccount.address)).to.equal(true);
  });

  it("Should prevent unauthorized callers from registering records", async function () {
    await expect(
      ledger.connect(unauthorizedAccount).registerRecord(mockHash1, "donation", "DON-001")
    ).to.be.revertedWith("Caller is not authorized to register audit records");
  });

  it("Should register an audit record and emit RecordRegistered event", async function () {
    await ledger.setCallerAuthorization(ngoAccount.address, true);

    await expect(ledger.connect(ngoAccount).registerRecord(mockHash1, "donation", "DON-001"))
      .to.emit(ledger, "RecordRegistered")
      .withArgs(mockHash1, "donation", "DON-001", ngoAccount.address, (val) => val > 0);

    const record = await ledger.verifyRecord(mockHash1);
    expect(record.exists).to.equal(true);
    expect(record.eventType).to.equal("donation");
    expect(record.referenceId).to.equal("DON-001");
    expect(record.submitter).to.equal(ngoAccount.address);
    expect(record.isVerified).to.equal(false);
  });

  it("Should verify a distribution on-chain upon QR scan confirmation", async function () {
    await ledger.registerRecord(mockHash2, "distribution", "DIST-999");

    await expect(ledger.verifyDistribution(mockHash2, "DIST-999"))
      .to.emit(ledger, "DistributionVerified")
      .withArgs(mockHash2, "DIST-999", owner.address, (val) => val > 0);

    const record = await ledger.verifyRecord(mockHash2);
    expect(record.isVerified).to.equal(true);
  });
});
