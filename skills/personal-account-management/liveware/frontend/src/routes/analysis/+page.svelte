<script lang="ts">
  import AnalysisSection from "$lib/components/AnalysisSection.svelte";
  import { getDashboardAppContext } from "$lib/app-context";
  import { dashboardController as controller } from "$lib/dashboard-controller.svelte";

  const { language, t } = getDashboardAppContext();
</script>

<AnalysisSection
  analysis={controller.analysis}
  analysisLaunching={controller.analysisLaunching}
  selectedMonth={controller.selectedMonth}
  {language}
  {t}
  onRun={() => controller.runAnalysis()}
/>
