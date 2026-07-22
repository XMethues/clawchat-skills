<script lang="ts">
  import WalletCardsIcon from "@lucide/svelte/icons/wallet-cards";
  import { Button } from "$lib/components/ui/button";

  type Props = {
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
    role?: "alert" | "status";
  };

  let { title, description, actionLabel, onAction, role }: Props = $props();
</script>

<div class="grid min-h-72 place-items-center rounded-lg border border-dashed bg-muted/30 p-8 text-center" {role} aria-live={role === "alert" ? "assertive" : undefined}>
  <div>
    <div class="mx-auto mb-4 grid size-12 place-items-center rounded-lg bg-muted text-muted-foreground" aria-hidden="true">
      <WalletCardsIcon size={21} strokeWidth={1.8} />
    </div>
    <h2 class="text-xl font-semibold tracking-tight">{title}</h2>
    <p class="mx-auto mt-2 max-w-xl text-muted-foreground">{description}</p>
    {#if actionLabel && onAction}
      <div class="mt-5">
        <Button variant="outline" onclick={onAction}>{actionLabel}</Button>
      </div>
    {/if}
  </div>
</div>
