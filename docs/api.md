The Catalog contains a REST API for accessing the resources in the catalog.

## Authentication

Authentication is done through a shared token between the Catalog and the Client. To create a token go to `/api/` and click on the `Create API token` button.

Each user can have one token and there is no expiry on the user of that token. You can delete and create a new token at any time, however this will cause any applications using the old token to fail authentication.

To use the authentication token, pass it through as a HTTP Header, example with `curl`:

```bash
-H `Authentication: Token YOUR_TOKEN HERE`
```

## URLs

* `/logs/api/list/`: List logs.
* `/logs/api/list/<int:pk>`: Details for an individual log.

## Pagination

Pagination for next and previous are included the list results, but appending `?page=X` to the end of the URL will take you to the next page.