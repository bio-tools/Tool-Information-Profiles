# Tool Information Profiles

A *tool information profile* is a JSON document which specifies which tool attributes - defined in [biotoolsSchema](https://github.com/bio-tools/biotoolsSchema) - should be specified for different types of tools within a set of tool descriptions.

Within a profile, biotoolsSchema [attributes](https://biotoolsschema.readthedocs.io/en/latest/biotoolsschema_elements.html#) may be specified for different [tool types](https://biotoolsschema.readthedocs.io/en/latest/controlled_vocabularies.html#tool-type) as:  
* **Mandatory** - the attribute **MUST** be defined
* **Recommended** - the attribute **SHOULD** be defined
* **Optional** - the attribute **MAY** be defined
* **Not applicable** - the attribute is not relevant to this tool set and **MUST NOT** be defined.

The key words "MUST", "MUST NOT", "SHOULD", and "MAY", and "OPTIONAL" are to be interpreted as described in [RFC 2119](http://www.ietf.org/rfc/rfc2119.txt):

* "MUST" means that the guideline is an absolute requirement of the specification.
* "MUST NOT" mean that the guideline is an absolute prohibition of the specification.
* "SHOULD" mean that there may exist valid reasons in particular circumstances to ignore a particular guideline, but the full implications must be understood and carefully weighed before doing so.
* "MAY mean that the guideline is truly optional; you can choose to follow it or not.

Tool information profiles **MUST** comply with the Tool Information Profile Schema (a JSON schema), which supports *all* of the biotoolsSchema attributes.

# Application
We anticipate the tool information profiles will be used by a tool description verification service which will provide a sustainable method for reporting on tool description quality within a corpus of tools.

It will take as input 1) a list of bio.tools tool IDs and 2) a tool information profile, and produce as output a report on the compliance of the tool descriptions to the standard, in human and machine-readable formats. Tool descriptions will be consumed in JSON format, *e.g.* by invoking the [bio.tools](https://bio.tools) API.

![toolDescriptionVerifier](assets/toolDescriptionVerifier.png)

# Documentation (for stable version 1.0.0)
Comprehensive documentation is available: 
* [Technical docs](http://bio-tools.github.io/Tool-Information-Profiles/) (built from files under [/stable/docs](https://github.com/bio-tools/Tool-Information-Profiles/tree/master/stable/docs))

# Files

File                           | Description
----                           | -----------
toolInfoProfileSchema_dev.json | Tool Information Profile Schema - dev version (JSON schema)
docs                           | Technical documentation - latest stable version.  Hosted [here](http://bio-tools.github.io/Tool-Information-Profiles/) (files copied from "stable" below)
profiles                       | Tool Information Profiles created thus far
stable                         | Current stable version of the schema + docs 
stable/examples                | Example Tool Information Profiles created using the schema (latest stable version)
versions                       | Older stable versions of the schema + docs
assets                         | Folder for images and other assets
README.md		       | This file


