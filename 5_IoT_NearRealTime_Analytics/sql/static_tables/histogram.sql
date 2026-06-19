CREATE EXTERNAL TABLE IF NOT EXISTS NAMESPACE_PLACEHOLDER.histogram (
  organizationId                          STRING,
  fieldOperationGUID                      STRING,
  machineGUID                             STRING,
  year                                    BIGINT,
  dayOfYear                               BIGINT,
  hourOfDay                               BIGINT,
  AreaWorked_cm2                          DOUBLE,
  AreaProductivity_ha_per_hr              DOUBLE,
  VehicleSpeed_km_per_hr                  DOUBLE,
  FuelRatePerHour_l_per_hr                DOUBLE,
  FuelTotal_l                             DOUBLE,
  FuelProductivity_l_per_ha               DOUBLE,
  DeltaTime_sec                           DOUBLE,
  ActiveTime_ms                           DOUBLE,
  SectionWeightedDeltaTime_sec            DOUBLE,
  AppliedArea_ha                          DOUBLE,
  SeedRateSeedsTarget_seeds_per_ha        DOUBLE,
  TotalSeedQuantityAppliedSeed_seeds      DOUBLE,
  SeedRateMassTarget_kg_per_ha            DOUBLE,
  TotalSeedQuantityAppliedMass_kg         DOUBLE,
  YieldMassPerArea_kg_per_ha              DOUBLE,
  YieldWetMassPerArea_kg_per_ha           DOUBLE,
  YieldMass_kg                            DOUBLE,
  YieldWetMass_kg                         DOUBLE,
  YieldVolumePerArea_bu_per_ha            DOUBLE,
  YieldVolume_bu                          DOUBLE,
  HarvestMoisture_prcnt                   DOUBLE,
  Turnout_prcnt                           DOUBLE,
  YieldSeedCottonMassPerArea_kg_per_ha    DOUBLE,
  YieldSeedCottonMass_kg                  DOUBLE,
  YieldLintMassPerArea_kg_per_ha          DOUBLE,
  YieldLintMass_kg                        DOUBLE,
  TotalQuantityAppliedVolume_l            DOUBLE,
  TotalQuantityTargetVolume_l             DOUBLE,
  AppRateVolumeTarget_l_per_ha            DOUBLE,
  AppRateVolumeMeasured_l_per_ha          DOUBLE,
  TillageDepthTarget_cm                   DOUBLE,
  TillageDepthMeasured_cm                 DOUBLE
)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
  LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3://STATIC_DATA_BUCKET_PLACEHOLDER/static/histogram/'
TBLPROPERTIES ('skip.header.line.count' = '1');
