---
department: engineering
author: dave
confidential: false
---

# API Design Guidelines

## Core Principles

1. **REST-based Design**

   - Use appropriate HTTP methods (GET, POST, PUT, DELETE)
   - Utilize proper status codes
   - Implement resource-based URLs

2. **Versioning**

   - Include version in URL path: `/api/v1/resource`
   - Maintain backward compatibility within major versions

3. **Authentication**
   - Use JWT for authentication
   - Implement OAuth 2.0 for third-party integrations
   - Rate limit by API key

## Request/Response Format

### Standard Response Format

```json
{
  "status": "success",
  "data": {},
  "message": "",
  "errors": []
}
```

### Pagination

```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "total": 100,
    "per_page": 20,
    "current_page": 1,
    "last_page": 5,
    "next_page_url": "/api/v1/resource?page=2",
    "prev_page_url": null
  }
}
```

## Error Handling

- Use appropriate HTTP status codes
- Provide detailed error messages
- Include error codes for frontend handling

Example:

```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": [
    {
      "field": "email",
      "code": "INVALID_FORMAT",
      "message": "Email must be a valid email address"
    }
  ]
}
```

## Security Considerations

1. Always validate and sanitize input
2. Implement proper CORS settings
3. Use HTTPS only
4. Add timeouts for all API calls
5. Limit payload size
6. Implement rate limiting

## API Documentation

- Use OpenAPI/Swagger for documentation
- Include example requests and responses
- Document all possible error responses
- Keep documentation in sync with implementation
