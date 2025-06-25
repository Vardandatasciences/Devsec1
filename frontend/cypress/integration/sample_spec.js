describe('My First Test', () => {
  it('Visits the app', () => {
    cy.visit('http://localhost:3000');  // Change this URL if necessary
    cy.contains('Welcome');  // Adjust this to match something on your app
  });
});
