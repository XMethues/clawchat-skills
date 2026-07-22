<script lang="ts">
  import SubscriptionsSection from "$lib/components/SubscriptionsSection.svelte";
  import { getDashboardAppContext } from "$lib/app-context";
  import { dashboardController as controller } from "$lib/dashboard-controller.svelte";

  const { language, t } = getDashboardAppContext();
</script>

{#if controller.book}
  <SubscriptionsSection book={controller.book} {language} {t} />
{/if}
