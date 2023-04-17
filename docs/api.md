The Catalog contains a REST API for accessing the resources in the catalog.

## Authentication

Authentication is done through a shared token between the Catalog and the Client. To create a token go to `/api/` and click on the `Create API token` button.

Each user can have one token and there is no expiry on the user of that token. You can delete and create a new token at any time, however this will cause any applications using the old token to fail authentication.

To use the authentication token, pass it through as a HTTP Header, example with `curl`:

```bash
-H `Authentication: Token YOUR_TOKEN HERE`
```

## URLs

**Note:** that the web interface uses `slug` for its URLs because those are more pleasant in a browser and to share. The API uses `pk` in its URLs as that's standard in Django Rest Framework.

* `GET /api/logs/list/`: List logs.
* `GET /api/logs/list/<int:pk>`: Details for an individual log.
* `GET /api/source/`: List sources.
* `POST /api/source/`: Create a source.
* `GET /api/source/<int:pk>/`: Details for a source.
* `DELETE /api/source/<int:pk>/`: Delete a source.
* `GET /api/source/<int:pk>/refresh`: Refresh a source.
* `GET /api/source/<int:pk>/validate`: Validate a source.

## Pagination

Pagination for next and previous are included the list results, but appending `?page=X` to the end of the URL will take you to the next page.

## Response codes

Service Catalog tries to follow the best practices for HTTP Response codes. If Service Catalog is getting an error back from a downstream service, such as GitHub, then it will return a `502` status code in the API.