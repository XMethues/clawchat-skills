<script lang="ts">
  import BottomNav from "$lib/components/BottomNav.svelte";
  import { formatMonth } from "$lib/format";
  import * as Select from "$lib/components/ui/select/index.js";
  import type { TranslationKey } from "$lib/i18n";
  import type { DashboardSection, Language } from "$lib/types";

  type Props = {
    language: Language;
    months: string[];
    selectedMonth: string;
    activeSection: DashboardSection;
    t: (key: TranslationKey) => string;
    onMonthChange: (month: string) => void;
  };

  let {
    language,
    months,
    selectedMonth,
    activeSection,
    t,
    onMonthChange,
  }: Props = $props();

  const monthItems = $derived(
    months.map((month) => ({ value: month, label: formatMonth(month, language) })),
  );
  const selectedMonthLabel = $derived(
    monthItems.find((month) => month.value === selectedMonth)?.label ?? selectedMonth,
  );
</script>

<header class="relative z-30 border-b bg-background md:sticky md:top-0 md:bg-background/95 md:backdrop-blur md:supports-[backdrop-filter]:bg-background/60">
  <div class="mx-auto flex min-h-14 w-full max-w-6xl items-center px-3 py-2 sm:px-4">
    <div class="flex w-full flex-col items-stretch gap-2 md:flex-row md:items-center md:gap-3">
      <Select.Root
        type="single"
        value={selectedMonth}
        items={monthItems}
        onValueChange={(value) => {
          if (value && value !== selectedMonth) onMonthChange(value);
        }}
      >
        <Select.Trigger class="w-full md:w-[180px] md:shrink-0" aria-label={t("month")}>
          {selectedMonthLabel}
        </Select.Trigger>
        <Select.Content>
          {#each monthItems as month (month.value)}
            <Select.Item value={month.value} label={month.label}>
              {month.label}
            </Select.Item>
          {/each}
        </Select.Content>
      </Select.Root>

      <BottomNav active={activeSection} {t} />
    </div>
  </div>
</header>
