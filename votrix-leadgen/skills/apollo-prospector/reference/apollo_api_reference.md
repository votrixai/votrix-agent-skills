# Apollo API Reference

## People Search Endpoint

**POST** `https://api.apollo.io/v1/mixed_people/search`

### Headers
```
Content-Type: application/json
X-Api-Key: <APOLLO_API_KEY>
```

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_titles` | array[string] | Job title keywords to match |
| `person_seniorities` | array[string] | Seniority levels: `owner`, `c_suite`, `vp`, `director`, `manager`, `senior`, `entry` |
| `person_locations` | array[string] | Location strings (e.g., "United States", "California") |
| `organization_industry_tag_ids` | array[string] | Industry filter IDs |
| `organization_num_employees_ranges` | array[string] | Ranges like `"1,10"`, `"11,20"`, `"21,50"`, `"51,100"`, `"101,200"`, `"201,500"`, `"501,1000"`, `"1001,2000"`, `"2001,5000"`, `"5001,10000"`, `"10001,1000000"` |
| `organization_locations` | array[string] | Company HQ locations |
| `q_organization_keyword_tags` | array[string] | Technology/keyword filters |
| `per_page` | integer | Results per page (max 100) |
| `page` | integer | Page number (1-based) |

### Response Structure

```json
{
  "people": [
    {
      "id": "string",
      "first_name": "string",
      "last_name": "string",
      "title": "string",
      "seniority": "string",
      "departments": ["string"],
      "email": "string",
      "email_status": "verified|guessed|unavailable",
      "linkedin_url": "string",
      "phone_numbers": [{"raw_number": "string"}],
      "organization": {
        "name": "string",
        "website_url": "string",
        "industry": "string",
        "estimated_num_employees": 100,
        "annual_revenue": 1000000,
        "city": "string",
        "state": "string",
        "country": "string",
        "linkedin_url": "string",
        "current_technologies": [{"name": "string"}]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total_entries": 500,
    "total_pages": 20
  }
}
```

### Rate Limits

- Standard: 50 requests/minute
- Pagination: Use `page` parameter, max 100 per page
- Credit cost: ~1 credit per person record accessed

### Employee Range Mapping

| ICP Range | Apollo Format |
|-----------|---------------|
| 1-10 | `"1,10"` |
| 11-50 | `"11,20"`, `"21,50"` |
| 51-200 | `"51,100"`, `"101,200"` |
| 201-500 | `"201,500"` |
| 501-2000 | `"501,1000"`, `"1001,2000"` |
| 2001-5000 | `"2001,5000"` |
| 5000+ | `"5001,10000"`, `"10001,1000000"` |

### Error Codes

| Code | Meaning |
|------|---------|
| 401 | Invalid API key |
| 422 | Invalid parameters |
| 429 | Rate limited — back off and retry |
| 500 | Server error — retry with backoff |
