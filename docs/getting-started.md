Once you've completed installation, you can start to add in entries into your repositories and have the catalog start to pull information in.

## Example organization

An [example organization](https://github.com/service-catalog-testing/) is available to highlight all the possible options that might exist for you. The fictional company `Burnt Tomatoes` will be used repeatedly throughout these examples.

## Source

For the Catalog, a source is a repository that hosts the configuration that it will read into the Catalog. Each source can contain any number of configuration files.

By default the Catalog will look in one of the following places in the Source repository:
* `catalog.json`
* `.service-catalog/catalog.json`
* `.github/catalog.json`

The file contents are validated against this [schema](https://github.com/clearwind-ca/service-catalog/blob/main/catalog/schemas/service.json).

Each `JSON` file then maps to one service.

## Service

For the Catalog, each Service is an element within your organisation.

The Catalog makes no requirements or definitions about how large or small or Service is or what it is. It could be an application, a team, a group of applications - whatever makes sense for you and your organisation.

Required fields:
* `name`: a name for the service.
* `priority`: a number from `1` to `10`. Where `1` is the highest priority, `10` being the lowest priority.
* `type`: a string that categorises the service for you in some manner that makes sense.

Optional fields:
* `description`: a text field that has more space for details about the service. Will be formatted using Markdown.
* `active`: a boolean to mark the service as active or not.
* `dependencies`: an array of strings, where each string is a slug of the service that is a dependency. See below for the slug 👇.
* `meta`: an object that allows you to enter any arbitrary detail. See below for more detail 👇.
* `files`: an array of strings, where each string is a path relative to the root of the repository that contains more catalog entries. See below for more detail 👇.

### Slugs

When a Service is added to the Catalog it is given a slug [using the built-in Django slug function](https://docs.djangoproject.com/en/4.1/ref/utils/#django.utils.text.slugify). For example: `Database Team` becomes `database-team`.

Slugs must be unique within the Service Catalog.

### Meta

The Service Catalog does not have any requirements or definitions for how Services within the Catalog should provide metadata. This is completely up to the organisation to decide. 

It's recommended that the `meta` contains information that is usefult to people in the organisation who might be unfamiliar with the service, or need to quickly find information in an incident.

Because your organization could be using Slack, Teams, Datadog, Splunk, GitHub, GitHub Enterprise etc., the `meta` field is deliberately vague and open ended for whatever makes sense for you.

See [configuration](configuration.md) for information on how to enforce `meta`.

### Files

One repository might have multiple services. To allow this the `files` array allows one repository to contain multiple services. If `files` is encountered in a file, the Service Catalog will pull information from that file.

The `files` array can be in any file read by the Service Catalog.

