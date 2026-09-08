/**
 * Truffle configuration for AgricLedger blockchain module
 * Supports local development with Ganache
 */

module.exports = {
  networks: {
    // Local development network (Ganache)
    development: {
      host: "127.0.0.1",
      port: 7545,
      network_id: "*", // Match any network id
      gas: 6721975,
      gasPrice: 20000000000, // 20 Gwei
    },
    // Local blockchain (for testing)
    local: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "5777",
    }
  },
  
  // Configure contract compiler
  compilers: {
    solc: {
      version: "0.8.0",
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        }
      }
    }
  },

  // Paths for contracts and migrations
  contracts_directory: './contracts',
  contracts_build_directory: './build/contracts',
  migrations_directory: './migrations',
};