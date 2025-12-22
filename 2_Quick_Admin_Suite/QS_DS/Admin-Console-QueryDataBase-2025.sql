SELECT
  -- Basic event fields
  q.eventversion,
  q.eventtime,
  q.eventsource,
  q.eventname,
  q.awsregion,
  q.sourceipaddress,
  q.useragent,
  q.errorcode,
  q.errormessage,
  q.requestparameters,
  q.responseelements,
  q.additionaleventdata,
  q.requestid,
  q.eventid,
  q.eventtype,
  q.apiversion,
  q.readonly,
  q.recipientaccountid,
  q.serviceeventdetails,
  q.sharedeventid,
  q.vpcendpointid,
  q.region,
  q.timestamp,
  q.datasourceid,
  q.queryid,
  q.dashboard_analysis,
  q.datasetid,
  q.datasetmode,

  -- Flattened useridentity
  q.useridentity.type AS useridentity_type,
  q.useridentity.principalid AS useridentity_principalid,
  q.useridentity.arn AS useridentity_arn,
  q.useridentity.accountid AS useridentity_accountid,
  q.useridentity.invokedby AS useridentity_invokedby,
  q.useridentity.accesskeyid AS useridentity_accesskeyid,
  q.useridentity.username AS useridentity_username,

  -- Useridentity session context attributes
  q.useridentity.sessioncontext.attributes.mfaauthenticated AS useridentity_mfa_authenticated,
  q.useridentity.sessioncontext.attributes.creationdate AS useridentity_session_creationdate,

  -- Useridentity session issuer
  q.useridentity.sessioncontext.sessionissuer.type AS sessionissuer_type,
  q.useridentity.sessioncontext.sessionissuer.principalid AS sessionissuer_principalid,
  q.useridentity.sessioncontext.sessionissuer.arn AS sessionissuer_arn,
  q.useridentity.sessioncontext.sessionissuer.accountid AS sessionissuer_accountid,
  q.useridentity.sessioncontext.sessionissuer.username AS sessionissuer_username,

  -- Flattened resources
  r_ordinal AS resource_index,
  r.arn AS resource_arn,
  r.accountid AS resource_accountid,
  r.type AS resource_type,
  ds.datasource_id AS ds_datasource_id_from_join,
  coalesce(json_extract_scalar(q.serviceeventdetails, '$.eventRequestDetails.databaseType'), ds.datasource_type) 
  AS databaseType

FROM 
(select *, regexp_extract(datasourceid,'datasource/(.*)') as sim_datasource_id 
from "admin-console-2025".quicksight_querydb_events) AS q
LEFT JOIN "admin-console-2025".datasource_property AS ds on q.sim_datasource_id = ds.datasource_id
LEFT JOIN UNNEST(q.resources)
     WITH ORDINALITY AS t(r, r_ordinal) ON TRUE