import sys

from pyspark import SQLContext

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import DataFrame, Row
import datetime
from awsglue import DynamicFrame
from pyspark.sql.session import SparkSession
from awsglue.context import GlueContext
from pyspark.sql.functions import json_tuple, from_json, get_json_object, to_timestamp



spark = SparkSession.builder.config('spark.serializer','org.apache.spark.serializer.KryoSerializer').config('spark.sql.hive.convertMetastoreParquet','false').config('hoodie.datasource.hive_sync.use_jdbc','false').getOrCreate()
sc = spark.sparkContext
glueContext = GlueContext(spark.sparkContext)


commonConfig = {'hoodie.datasource.write.hive_style_partitioning' : 'true','className' : 'org.apache.hudi', 'hoodie.datasource.hive_sync.use_jdbc':'false', 'hoodie.datasource.write.precombine.field': 'id', 'hoodie.datasource.write.recordkey.field': 'id', 'hoodie.table.name': 'cust_hudi_f1', 'hoodie.consistency.check.enabled': 'true', 'hoodie.datasource.hive_sync.database': 'default', 'hoodie.datasource.hive_sync.table': 'cust_hudi_f1', 'hoodie.datasource.hive_sync.enable': 'true', 'path': 's3://' + 'x14lambdasource/Unsaved' + '/cust_hudi/test_data_20'}
partitionDataConfig = { 'hoodie.datasource.write.keygenerator.class' : 'org.apache.hudi.keygen.ComplexKeyGenerator', 'hoodie.datasource.write.partitionpath.field': "partitionkey, partitionkey2 ", 'hoodie.datasource.hive_sync.partition_extractor_class': 'org.apache.hudi.hive.MultiPartKeysValueExtractor', 'hoodie.datasource.hive_sync.partition_fields': "partitionkey, partitionkey2"}
incrementalConfig = {'hoodie.upsert.shuffle.parallelism': 68, 'hoodie.datasource.write.operation': 'upsert', 'hoodie.cleaner.policy': 'KEEP_LATEST_COMMITS', 'hoodie.cleaner.commits.retained': 2}

combinedConf = {**commonConfig, **partitionDataConfig, **incrementalConfig}

glue_temp_storage = "s3://x14lambdasource/Unsaved"

data_frame_DataSource0 = glueContext.create_data_frame.from_catalog(database = "default", table_name = "test_cdc_cust", transformation_ctx = "DataSource0", additional_options = {"startingPosition": "TRIM_HORIZON", "inferSchema": "true"})

def processBatch(data_frame, batchId):
    if (data_frame.count() > 0):

        DataSource0 = DynamicFrame.fromDF(data_frame, glueContext, "from_data_frame")
        DataSource0.toDF().show()
        
        your_map = [
            ('eventName', 'string', 'eventName', 'string'),
            ('userIdentity', 'string', 'userIdentity', 'string'),
            ('eventSource', 'string', 'eventSource', 'string'),
            ('tableName', 'string', 'tableName', 'string'),
            ('recordFormat', 'string', 'recordFormat', 'string'),
            ('eventID', 'string', 'eventID', 'string'),
            ('dynamodb.ApproximateCreationDateTime', 'long', 'ApproximateCreationDateTime', 'long'),
            ('dynamodb.SizeBytes', 'long', 'SizeBytes', 'long'),
            ('dynamodb.NewImage.id.S', 'string', 'id', 'string'),
            ('dynamodb.NewImage.custName.S', 'string', 'custName', 'string'),
            ('dynamodb.NewImage.email.S', 'string', 'email', 'string'),
            ('dynamodb.NewImage.registrationDate.S', 'string', 'registrationDate', 'string'),
            ('awsRegion', 'string', 'awsRegion', 'string')
        ]

        new_df = ApplyMapping.apply(frame = DataSource0, mappings=your_map, transformation_ctx = "applymapping1")
        abc = new_df.toDF()
        inputDf = abc.withColumn('update_ts_dms',to_timestamp(abc["registrationDate"])).withColumn('partitionkey',abc["id"].substr(-1,1)).withColumn('partitionkey2',abc["id"].substr(-2,1))
        
        
        inputDf.printSchema()
        inputDf.show()

        # glueContext.write_dynamic_frame.from_options(frame = DynamicFrame.fromDF(inputDf, glueContext, "inputDf"), connection_type = "marketplace.spark", connection_options = combinedConf)
        glueContext.write_dynamic_frame.from_options(frame = DynamicFrame.fromDF(inputDf, glueContext, "inputDf"), connection_type = "custom.spark", connection_options = combinedConf)


glueContext.forEachBatch(frame = data_frame_DataSource0, batch_function = processBatch, options = {"windowSize": "100 seconds", "checkpointLocation":  "s3://x14lambdasource/Unsaved/checkpoint1/"})
