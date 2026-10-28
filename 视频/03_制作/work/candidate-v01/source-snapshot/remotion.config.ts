import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.overrideWebpackConfig((currentConfiguration) => ({
  ...currentConfiguration,
  resolve: {
    ...currentConfiguration.resolve,
    modules: [
      "/Users/henry/.shared/.skill-runtime-deps/node_modules/ai-coach-daily-demo__remotion__node_modules",
      ...(currentConfiguration.resolve?.modules ?? []),
    ],
  },
}));
