<script lang="ts">
  import { Badge, Button, Modal } from "flowbite-svelte";
  import { CalendarEditOutline, CheckCircleSolid } from "flowbite-svelte-icons";
  import { getColor } from "$lib/utils/colourGenerator";
  import { ArrowLeftOutline, ArrowRightOutline } from "flowbite-svelte-icons";
  import {
    isEqualListObject,
    type ListObject,
  } from "$lib/apis/parcel/api.parcel";
  import { onMount } from "svelte";

  export let list1: ListObject[];
  export let list2: ListObject[];
  export let open: boolean = false;
  export let title1: string = "QP Options";
  export let title2: string = "Selected QP Options";
  export let headerTitle: string = "Choose the QPs for this contract";
  export let onOkayClicked: (list: ListObject[]) => void;

  let uniqueList1: ListObject[] = [];

  function handleOk() {
    onOkayClicked(list2);
  }

  onMount(() => {
    updateUniqueList1();
  });
  function updateUniqueList1() {
    uniqueList1 = list1.filter(
      (item) => !list2.some((i) => isEqualListObject(i, item)),
    );
  }

  function addToList2(item: ListObject) {
    console.log(`adding ${item.display} to list2`);
    list2 = [...list2, item];
    uniqueList1 = uniqueList1.filter((i) => !isEqualListObject(i, item));
  }

  function removeFromList2(item: ListObject) {
    list2 = list2.filter((i) => !isEqualListObject(i, item));
    uniqueList1 = [...uniqueList1, item];
  }
</script>

<Modal bind:open size="lg" autoclose class="w-50%">
  <div class="text-center">
    <CalendarEditOutline
      class="mx-auto mb-4 h-12 w-12 text-gray-400 dark:text-gray-200"
    />
    <h3 class="mb-5 text-lg font-normal text-gray-500 dark:text-gray-400">
      {headerTitle}
    </h3>

    <div class="flex">
      <div class="w-1/2 p-2">
        <h2 class="mb-4 text-lg font-bold">{title1}</h2>
        <div class="grid grid-cols-1">
          {#each uniqueList1 as item, index}
            <div>
              <Badge
                dismissable
                color={getColor(index)}
                class="mb-2 mr-2 cursor-pointer"
                on:close={() => addToList2(item)}
                on:click={close}
                aria-label="Remove"
              >
                <button
                  slot="close-button"
                  let:close
                  on:click={() => {
                    addToList2(item);
                    close;
                  }}
                  type="button"
                  aria-label="Remove"
                >
                  <span
                    class="test-select-shipment-button flex justify-center overflow-hidden text-ellipsis whitespace-nowrap max-w-xs"
                  >
                    {item.display}
                    <CheckCircleSolid class="ml-2" />
                  </span>
                </button>
              </Badge>
            </div>
          {/each}
        </div>
      </div>
      <div class="flex items-center">
        <div>
          <ArrowRightOutline />
          <ArrowLeftOutline />
        </div>
      </div>
      <div class="w-1/2 p-2">
        <h2 class="mb-4 text-lg font-bold">{title2}</h2>
        <div class="grid grid-cols-1">
          {#each list2 as item, index}
            <div>
              <Badge
                dismissable
                color={getColor(index)}
                class="mb-2 mr-2 cursor-pointer"
                on:click={close}
                aria-label="Remove"
              >
                <button
                  slot="close-button"
                  let:close
                  on:click={() => {
                    removeFromList2(item);
                    close;
                  }}
                  type="button"
                  aria-label="Remove"
                >
                  <span
                    class="flex justify-center overflow-hidden text-ellipsis whitespace-nowrap max-w-xs"
                  >
                    {item.display}
                    <CheckCircleSolid class="ml-2" />
                  </span>
                </button>
              </Badge>
            </div>
          {/each}
        </div>
      </div>
    </div>
    <Button color="red" class="me-2" on:click={handleOk}>ok</Button>
  </div>
</Modal>
