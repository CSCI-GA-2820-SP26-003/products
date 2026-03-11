# Products REST API Service

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![Build Status](https://github.com/2022mc12/products/actions/workflows/ci.yml/badge.svg)](https://github.com/2022mc12/products/actions)

## Overview

This microservice provides a RESTful interface for managing a product catalog. It allows you to Create, Read, List, Update, and Delete product records stored in the underlying database.

The service is built using the Flask web framework and follows standard REST patterns. It handles JSON payloads and returns appropriate HTTP status codes for all operations.

## API Endpoints

The following endpoints are available. All request bodies must be sent as application/json.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/` | Returns API details, version, and available endpoints. |
| **GET** | `/products` | Returns a list of all products. |
| **POST** | `/products` | Creates a new product with the provided JSON data. |
| **GET** | `/products/<id>` | Returns a single product based on its ID. |
| **PUT** | `/products/<id>` | Updates a product's data based on its ID. |
| **DELETE** | `/products/<id>` | Deletes a product from the database. |

## Usage Examples (CLI)

### 1. Create a Product

**POST** `/products`

```bash
curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{
          "name": "My Amazing Product",
          "sku": "CAT-001",
          "description": "Tell us how wonderful your product is!",
          "price": 99.99,
          "image_url": "example.com/assets/image-of-your-product.jpg"
         }'
```

### 2. List Products

**GET** `/products`

`curl -X GET http://localhost:8080/products`

### 3. Get a Product

**GET** `/products/<id>`

`curl -X GET http://localhost:8080/products/<id>`

### 4. Update a Product

**PUT** `/products/<id>`

`curl -X PUT http://localhost:8080/products/<id> -H "Content-Type: application/json" -d '{"price": 89.99}'`

### 5. Create a Product

**DELETE** `/products/<id>`

`curl -X DELETE http://localhost:8080/products/<id>`

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
