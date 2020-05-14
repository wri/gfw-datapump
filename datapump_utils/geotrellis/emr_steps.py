import os


class StepList:
    def __init__(self, output_url):
        self.steps = []
        self.output_url = output_url

    def add_step(
        self,
        analysis,
        feature_type,
        feature_sources,
        action_on_failure="CONTINUE",
        summary=True,
        fire_type=None,
        fire_sources=[],
    ):
        step = Step(
            analysis,
            feature_type,
            feature_sources,
            self.output_url,
            action_on_failure,
            summary,
            fire_type,
            fire_sources,
        )
        self.steps.append(step)

    def to_serializable(self):
        return [step.to_serializable() for step in self.steps]


class Step:
    def __init__(
        self,
        analysis,
        feature_type,
        feature_sources,
        output_url,
        action_on_failure="TERMINATE_CLUSTER",
        summary=True,
        fire_type=None,
        fire_sources=[],
    ):
        self.analysis = analysis
        self.action_on_failure = action_on_failure
        if feature_sources is not list:
            feature_sources = [feature_sources]

        if fire_sources is not list:
            fire_sources = [fire_sources]

        self.step_args = [
            "spark-submit",
            "--deploy-mode",
            "cluster",
            "--class",
            "org.globalforestwatch.summarystats.SummaryMain",
            os.environ["GEOTRELLIS_JAR"],
            "--analysis",
            analysis,
            "--feature_type",
            feature_type,
            "--output",
            output_url,
        ]

        for src in feature_sources:
            self.step_args.append("--features")
            self.step_args.append(src)

        if "annualupdate" in analysis:
            self.step_args.append("--tcl")
        elif analysis == "gladalerts":
            self.step_args.append("--glad")

        if not summary:
            self.step_args.append("--change_only")

        if fire_type and fire_sources:
            self.step_args.append("--fire_alert_type")
            self.step_args.append(fire_type)

            for src in fire_sources:
                self.step_args.append("--fire_alert_source")
                self.step_args.append(src)

    def to_serializable(self):
        return {
            "Name": self.analysis,
            "ActionOnFailure": self.action_on_failure,
            "HadoopJarStep": {"Jar": "command-runner.jar", "Args": self.step_args},
        }
