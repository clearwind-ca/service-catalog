Events are key events that occur in your organisation, such as (but not limited to):
* Deployments
* Releases
* Feature flag changes
* Migrations or transitions in databases
* Patches
* Roll backs

And so on. These are critical or important events in your infrastructure that are heplful to you in incidents or tracking down bugs. Other services exist to provide high volume, low latency logging and querying capabilities.

## Out of the box events

If in the `catalog.json` your service defines some events values, those will **automatically** be entered into the Events list. Example:

```json
"events": {"deployments", "releases"}
```

In this example both deployment and releases will be sent from GitHub to the Service Catalog, as webhooks and automatically added to the events timeline. 

If the deployment is to the `production` environment then `Affects customers` is set to true.

If the release is not a pre-release then `Affect customers` is set to true.

## Authentication

In order to send an even to the Service Catalog, you must authenticate with [the API](api.md) and to do that, you will need the API token for a user logged into the Service Catalog. In the following example 👇, it assumes the Secret is called `SERVICE_CATALOG_TOKEN`.

## Example GitHub Action

You can easily send an event to the Service Catalog using the [create-event Action](https://github.com/clearwind-ca/create-event)

```yaml
    - uses: clearwind-ca/create-event@v1
      env:
        SERVICE_CATALOG_TOKEN: ${{ secrets.SERVICE_CATALOG_TOKEN }}
      with:
        catalog_url: "https://url-to-your-service-catalog.com"
        name: A test deployment
        type: Deployment
        source: GitHub Action
```

In this case an event will be created with following values:
* `catalog_url`: the URL to the deployment.
* `type`: the type of event, in this case a deployment.
* `source`: what service triggered this event.
 
## Future events

You can also add events in the future. These are useful to communicate maintenance windows, or planned events that may impact services across the organisation.
