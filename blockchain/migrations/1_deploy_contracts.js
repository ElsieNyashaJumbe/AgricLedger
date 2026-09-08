/**
 * Migration script to deploy AgricLedger contracts
 */

const DataSovereignty = artifacts.require("DataSovereignty");
const LandTenure = artifacts.require("LandTenure");

module.exports = function(deployer) {
  // Deploy DataSovereignty contract first
  deployer.deploy(DataSovereignty)
    .then(() => {
      console.log("✅ DataSovereignty deployed at:", DataSovereignty.address);
    });
  
  // Deploy LandTenure contract
  deployer.deploy(LandTenure)
    .then(() => {
      console.log("✅ LandTenure deployed at:", LandTenure.address);
    });
};