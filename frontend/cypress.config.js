module.exports = {
  e2e: {
    supportFile: false,  // Disable the support file if not needed
    baseUrl: 'http://localhost:3000',  // Adjust as needed
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
  },
  component: {
    devServer: {
      framework: 'vue', // Adjust as needed
      bundler: 'vite',  // Adjust as needed
    },
  },
};
