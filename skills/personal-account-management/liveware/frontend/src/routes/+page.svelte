<script lang="ts">
  import OverviewSection from "$lib/components/OverviewSection.svelte";
  import { getDashboardAppContext } from "$lib/app-context";
  import { dashboardController as controller } from "$lib/dashboard-controller.svelte";

  const { language, t } = getDashboardAppContext();
</script>

{#if controller.book}
  <OverviewSection book={controller.book} {language} {t} />
{/if}
