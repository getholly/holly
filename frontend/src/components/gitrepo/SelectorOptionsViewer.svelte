<script lang="ts">
  import { Tabs, TabItem } from "flowbite-svelte";
  import Option2_Accordion from "$components/gitrepo/Option2_Accordion.svelte";
  import Option3_TwoPanel from "$components/gitrepo/Option3_TwoPanel.svelte";
  import Option4_TagsModal from "$components/gitrepo/Option4_TagsModal.svelte";
  import Option5_CardGrid from "$components/gitrepo/Option5_CardGrid.svelte";
  import GitMultiSelect from "$components/gitrepo/GitMultiSelect.svelte";

  let activeTab = 0; // Index of the active tab
</script>

<svelte:head>
  <title>Repo/Branch Selector Options</title>
</svelte:head>

<div class="container mx-auto p-4">
  <h1 class="text-2xl font-bold mb-4">
    GitHub Repository & Branch Selector Options
  </h1>

  <Tabs bind:activeKey={activeTab} class="mb-4">
    <TabItem open={activeTab === 0}>
      <span slot="title">1. Multi-Select</span>
      <GitMultiSelect />
    </TabItem>
    <TabItem open={activeTab === 1}>
      <span slot="title">2. Accordion</span>
      <Option2_Accordion />
    </TabItem>
    <TabItem open={activeTab === 2}>
      <span slot="title">3. Two Panel</span>
      <Option3_TwoPanel />
    </TabItem>
    <TabItem open={activeTab === 3}>
      <span slot="title">4. Tags + Modal</span>
      <Option4_TagsModal />
    </TabItem>
    <TabItem open={activeTab === 4}>
      <span slot="title">5. Card Grid</span>
      <Option5_CardGrid />
    </TabItem>
  </Tabs>
</div>
