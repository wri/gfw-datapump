public class MockGeotrellis {
    public static void main(String[] args) throws Exception {
        String joined = String.join(" ", args);
        String expectedGladUpdateStep = "spark-submit --deploy-mode cluster --class org.globalforestwatch.summarystats.SummaryMain s3://gfw-pipelines-test/geotrellis/jars/treecoverloss-assembly-1.2.1.jar --analysis gladalerts --output s3://gfw-pipelines-test/geotrellis/results/vteststats1/test_zonal_stats --features s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv --feature_type feature --glad";
        String expectedGladSyncStep = "spark-submit --deploy-mode cluster --class org.globalforestwatch.summarystats.SummaryMain s3://gfw-pipelines-test/geotrellis/jars/treecoverloss-assembly-1.2.1.jar --analysis gladalerts --output s3://gfw-pipelines-test/geotrellis/results/v20210122/test_zonal_stats/glad --features s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv --feature_type feature --glad --change_only";
        String expectedIntegratedAlertsSyncStep = "spark-submit --deploy-mode cluster --class org.globalforestwatch.summarystats.SummaryMain s3://gfw-pipelines-test/geotrellis/jars/treecoverloss-assembly-1.2.1.jar --analysis integrated_alerts --output s3://gfw-pipelines-test/geotrellis/results/v20210122/test_zonal_stats/integrated_alerts --features s3://gfw-pipelines-test/test_zonal_stats/vtest1/vector/epsg-4326/test_zonal_stats_vtest1_1x1.tsv --feature_type feature --glad";

        System.out.println(joined);

        if (!joined.equals(expectedGladUpdateStep) && !joined.equals(expectedGladSyncStep) && !joined.equals(expectedIntegratedAlertsSyncStep)) {
            throw new Exception("Invalid step args");
        }
    }
}
