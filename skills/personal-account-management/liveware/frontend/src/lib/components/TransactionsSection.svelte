<script lang="ts">
  import ArrowLeftIcon from "@lucide/svelte/icons/arrow-left";
  import ArrowRightIcon from "@lucide/svelte/icons/arrow-right";
  import SearchIcon from "@lucide/svelte/icons/search";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { Input } from "$lib/components/ui/input";
  import * as Select from "$lib/components/ui/select/index.js";
  import { formatDate, formatInteger, formatMoneyWithCode } from "$lib/format";
  import type { TranslationKey } from "$lib/i18n";
  import { selectTransactions } from "$lib/selectors";
  import type { BookResponse, KindFilter, Language, Transaction } from "$lib/types";

  type Props = {
    book: BookResponse;
    language: Language;
    t: (key: TranslationKey) => string;
    search: string;
    kindFilter: KindFilter;
    accountFilter: string;
    page: number;
    pageSize: number;
    onSearch: (value: string) => void;
    onKindFilter: (value: KindFilter) => void;
    onAccountFilter: (value: string) => void;
    onPage: (value: number) => void;
  };

  let {
    book,
    language,
    t,
    search,
    kindFilter,
    accountFilter,
    page,
    pageSize,
    onSearch,
    onKindFilter,
    onAccountFilter,
    onPage,
  }: Props = $props();

  const accounts = $derived(book.account_snapshot.accounts);
  const accountNames = $derived(new Map(accounts.map((account) => [account.id, account.name])));
  const allAccountsValue = "__all_accounts__";
  const accountItems = $derived([
    { value: allAccountsValue, label: t("allAccounts") },
    ...(accountFilter && !accountNames.has(accountFilter)
      ? [{ value: accountFilter, label: t("unavailableAccount") }]
      : []),
    ...accounts.map((account) => ({ value: account.id, label: account.name })),
  ]);
  const selectedAccountValue = $derived(accountFilter || allAccountsValue);
  const selectedAccountLabel = $derived(
    accountItems.find((account) => account.value === selectedAccountValue)?.label
      ?? t("allAccounts"),
  );
  const transactionPage = $derived(selectTransactions(book, {
    search,
    kind: kindFilter,
    accountId: accountFilter,
    page,
    pageSize,
  }));

  $effect(() => {
    if (transactionPage.page !== page) onPage(transactionPage.page);
  });

  const kinds: { value: KindFilter; label: TranslationKey }[] = [
    { value: "all", label: "filterAll" },
    { value: "income", label: "income" },
    { value: "expense", label: "expense" },
    { value: "transfer", label: "transfer" },
    { value: "review", label: "needsReview" },
  ];

  function accountLabel(id: string | null | undefined): string {
    return id ? (accountNames.get(id) ?? t("unknownAccount")) : t("unknownAccount");
  }

  function kindLabel(transaction: Transaction): string {
    if (transaction.kind === "income") return t("income");
    if (transaction.kind === "transfer") return t("transfer");
    return t("expense");
  }

  function signedAmount(transaction: Transaction): string {
    const amount = formatMoneyWithCode(transaction.amount_minor, transaction.currency, language);
    if (transaction.kind === "income") return `+${amount}`;
    if (transaction.kind === "expense") return `−${amount}`;
    return amount;
  }
</script>

<section class="grid gap-4" aria-labelledby="transactions-title">
  <div class="flex items-end justify-between gap-4 max-[45rem]:flex-col max-[45rem]:items-start">
    <div>
      <p class="mb-0.5 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">{formatInteger(transactionPage.total_items, language)} {t("records")}</p>
      <h2 id="transactions-title" class="text-3xl font-semibold tracking-tight sm:text-4xl">{t("transactionsTitle")}</h2>
      <p class="mt-1 max-w-2xl text-muted-foreground">{t("transactionsDescription")}</p>
    </div>
  </div>

  <Card.Root>
    <Card.Content class="grid items-end gap-3 lg:grid-cols-[minmax(16rem,1fr)_minmax(10rem,0.35fr)_auto]">
      <label class="relative block">
        <span class="sr-only">{t("searchTransactions")}</span>
        <SearchIcon class="pointer-events-none absolute top-1/2 left-3 z-10 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
        <Input
          class="pl-9"
          type="search"
          value={search}
          placeholder={t("searchPlaceholder")}
          oninput={(event) => onSearch(event.currentTarget.value)}
        />
      </label>
      <div class="grid gap-1">
        <span class="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">{t("account")}</span>
        <Select.Root
          type="single"
          value={selectedAccountValue}
          items={accountItems}
          onValueChange={(value) => {
            if (value) onAccountFilter(value === allAccountsValue ? "" : value);
          }}
        >
          <Select.Trigger class="w-full" aria-label={t("account")}>
            {selectedAccountLabel}
          </Select.Trigger>
          <Select.Content>
            {#each accountItems as account (account.value)}
              <Select.Item value={account.value} label={account.label}>
                {account.label}
              </Select.Item>
            {/each}
          </Select.Content>
        </Select.Root>
      </div>
      <fieldset class="no-scrollbar m-0 flex min-w-0 gap-1 overflow-x-auto border-0 pb-px">
        <legend class="sr-only">{t("transactionTypeFilter")}</legend>
        {#each kinds as kind (kind.value)}
          <Button
            size="sm"
            variant={kindFilter === kind.value ? "default" : "ghost"}
            aria-pressed={kindFilter === kind.value}
            onclick={() => onKindFilter(kind.value)}
          >
            {t(kind.label)}
          </Button>
        {/each}
      </fieldset>
    </Card.Content>
  </Card.Root>

  {#if transactionPage.total_items === 0}
    <Card.Root>
      <Card.Content class="grid min-h-56 place-items-center text-center">
        <div>
          <h3 class="text-xl font-semibold tracking-tight">{transactionPage.source_items === 0 ? t("noTransactions") : t("noMatchingTransactions")}</h3>
          <p class="mx-auto mt-2 max-w-xl text-muted-foreground">{transactionPage.source_items === 0 ? t("noTransactionsDescription") : t("noMatchingDescription")}</p>
        </div>
      </Card.Content>
    </Card.Root>
  {:else}
    <div class="overflow-hidden rounded-lg border bg-card">
      {#each transactionPage.items as transaction (transaction.id)}
        <article class="grid grid-cols-[8.5rem_minmax(0,1fr)_minmax(9rem,auto)] items-center gap-4 border-b p-4 last:border-b-0 max-[45rem]:grid-cols-[1fr_auto]" data-kind={transaction.kind}>
          <div class="grid min-w-0 max-[45rem]:col-span-full max-[45rem]:grid-cols-[auto_auto] max-[45rem]:justify-between">
            <span class="font-mono text-xs">{formatDate(transaction.date, language)}</span>
            <small class="text-xs text-muted-foreground">{kindLabel(transaction)}</small>
          </div>
          <div class="grid min-w-0">
            <div class="flex min-w-0 items-center gap-2">
              <strong class="break-words">{transaction.title}</strong>
              {#if transaction.needs_review}
                <Badge variant="outline">{t("needsReview")}</Badge>
              {/if}
            </div>
            <p class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground [&>span]:min-w-0 [&>span]:break-words">
              {#if transaction.merchant}<span>{transaction.merchant}</span>{/if}
              <span>{transaction.category}</span>
              {#if transaction.kind === "transfer"}
                <span>{accountLabel(transaction.account_id)} → {accountLabel(transaction.to_account_id)}</span>
              {:else}
                <span>{accountLabel(transaction.account_id)}</span>
              {/if}
            </p>
          </div>
          <div class="grid min-w-0 max-w-36 justify-items-end gap-0.5 text-right">
            <strong class="break-words font-mono text-sm" class:text-primary={transaction.kind === "income"} class:text-destructive={transaction.kind === "expense"}>{signedAmount(transaction)}</strong>
            {#if typeof transaction.base_amount_minor === "number"
              && transaction.base_currency
              && transaction.base_currency !== transaction.currency}
              <span class="max-w-full break-words text-xs text-muted-foreground">{t("recordedBase")}: {formatMoneyWithCode(transaction.base_amount_minor, transaction.base_currency, language)}</span>
            {/if}
          </div>
        </article>
      {/each}
    </div>

    <nav class="flex items-center justify-center gap-3" aria-label={t("transactionPages")}>
      <Button
        variant="outline"
        size="icon"
        aria-label={t("previousPage")}
        disabled={transactionPage.page <= 1}
        onclick={() => onPage(transactionPage.page - 1)}
      >
        <ArrowLeftIcon aria-hidden="true" />
      </Button>
      <span class="min-w-24 text-center font-mono text-xs text-muted-foreground">
        {t("page")} {transactionPage.page} / {transactionPage.total_pages}
      </span>
      <Button
        variant="outline"
        size="icon"
        aria-label={t("nextPage")}
        disabled={transactionPage.page >= transactionPage.total_pages}
        onclick={() => onPage(transactionPage.page + 1)}
      >
        <ArrowRightIcon aria-hidden="true" />
      </Button>
    </nav>
  {/if}
</section>
