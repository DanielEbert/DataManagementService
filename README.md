
### Requirements

- add measurements
- add collections
- get/query measurements based on id, name and metadata
- add/modify/delete metadata
    - e.g. key-value
    - value can be any string or e.g. link to file in blob storage
- trigger other jobs, e.g. recompute + KPI evaluation
- regular database backups

nice to have:
- simple GUI, e.g.:
    - to start recompute + KPI evaluation
    - links to other services, e.g.:
        - measurement has link to SIA visu & bytesoup in azure blob storage
        - job run has link to argo & output directory in blob storage
- validity checks, e.g. when adding a measurement: check if filename matches regex pattern


### User Stories

#### Add Measurement

- store bytesoup in blob storage (folder)
- add entry in measurement table

#### Add Metadata

- measurement name
- key=value
- or upload file in blob storage, value is link

#### Sequence

- create
- update/add
- delete
