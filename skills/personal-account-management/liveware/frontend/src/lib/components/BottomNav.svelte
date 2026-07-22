<script lang="ts">
  import ChartNoAxesCombinedIcon from "@lucide/svelte/icons/chart-no-axes-combined";
  import CreditCardIcon from "@lucide/svelte/icons/credit-card";
  import ListChecksIcon from "@lucide/svelte/icons/list-checks";
  import SparklesIcon from "@lucide/svelte/icons/sparkles";
  import type { TranslationKey } from "$lib/i18n";
  import type { DashboardSection } from "$lib/types";

  type Item = {
    id: DashboardSection;
    href: string;
    label: TranslationKey;
    icon: typeof ChartNoAxesCombinedIcon;
  };
  type Props = {
    active: DashboardSection;
    t: (key: TranslationKey) => string;
  };

  let { active, t }: Props = $props();

  const items: Item[] = [
    { id: "overview", href: "#/", label: "navOverview", icon: ChartNoAxesCombinedIcon },
    { id: "transactions", href: "#/transactions", label: "navTransactions", icon: ListChecksIcon },
    { id: "subscriptions", href: "#/subscriptions", label: "navSubscriptions", icon: CreditCardIcon },
    { id: "analysis", href: "#/analysis", label: "navAnalysis", icon: SparklesIcon },
  ];
</script>

<nav
  class="flex w-full items-center gap-1 rounded-lg border bg-card p-1 md:w-auto md:rounded-md md:border-0 md:bg-muted/60"
  aria-label={t("sectionNavigation")}
>
  {#each items as item (item.id)}
    {@const Icon = item.icon}
    <a
      class="inline-flex min-h-12 flex-1 cursor-pointer flex-col items-center justify-center gap-1 rounded-md px-1 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground active:translate-y-px aria-[current=page]:bg-primary aria-[current=page]:text-primary-foreground md:min-h-8 md:flex-none md:flex-row md:gap-1.5 md:px-3 md:py-1.5"
      href={item.href}
      aria-current={active === item.id ? "page" : undefined}
      aria-label={t(item.label)}
    >
      <Icon class="size-4" aria-hidden="true" />
      <span class="text-center text-[0.7rem] leading-tight sm:text-xs">{t(item.label)}</span>
    </a>
  {/each}
</nav>
