<script lang="ts">
  import TransactionsSection from "$lib/components/TransactionsSection.svelte";
  import { getDashboardAppContext } from "$lib/app-context";
  import { dashboardController as controller } from "$lib/dashboard-controller.svelte";

  const { language, t } = getDashboardAppContext();
</script>

{#if controller.book}
  <TransactionsSection
    book={controller.book}
    {language}
    {t}
    search={controller.search}
    kindFilter={controller.kindFilter}
    accountFilter={controller.accountFilter}
    page={controller.page}
    pageSize={controller.pageSize}
    onSearch={(value) => controller.setSearch(value)}
    onKindFilter={(value) => controller.setKindFilter(value)}
    onAccountFilter={(value) => controller.setAccountFilter(value)}
    onPage={(value) => controller.setPage(value)}
  />
{/if}
