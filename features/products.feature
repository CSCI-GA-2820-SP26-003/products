


Feature: The product service back-end
    As a Developer
    I need a RESTful catalog service
    So that I can keep track of all my products

Background:
    Given the following products
| name                  | sku                       | description                   | price   | category            | available |
| Black BIC Pen         | PEN-BLK-BIC-001           | Black BIC Pen                 | 0.50    | Writing Instruments | True      |



Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Product Demo RESTful Service" in the title
    And I should not see "404 Not Found"

Scenario: Read a Product
    When I visit the "Home Page"
    And I set the "Name" to "Black BIC Pen"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Black BIC Pen" in the "Name" field
Scenario: List all products via UI
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "Black BIC Pen" in the results


Scenario: Create a product via UI
    When I visit the "Home Page"
    And I set the "Name" to "Blue Pen"
    And I set the "SKU" to "PEN-BLU-001"
    And I set the "Description" to "Blue Pen"
    And I set the "Price" to "1.25"
    And I set the "Category" to "Writing Instruments"
    And I press the "Create" button
    Then I should see the message "Success"


Scenario: Update a product via UI
    When I visit the "Home Page"
    And I set the "Name" to "Black BIC Pen"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Black BIC Pen" in the "Name" field
    When I set the "Name" to "Red BIC Pen"
    And I set the "Description" to "Red BIC Pen"
    And I set the "Price" to "0.75"
    And I press the "Update" button
    Then I should see the message "Success"
    And I should see "Red BIC Pen" in the "Name" field
    And I should see "Red BIC Pen" in the "Description" field
    And I should see "0.75" in the "Price" field
