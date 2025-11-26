<script lang="ts">
  import { Card, Button, Avatar } from "flowbite-svelte";
  import {
    AnnotationOutline,
    CogOutline,
    FileCloneOutline,
    GlobeOutline,
    LockOutline,
    PhoneOutline,
    ShareAllOutline,
    UsersGroupOutline,
  } from "flowbite-svelte-icons";
  import Chat from "$components/chat/Chat.svelte";
  import { currentChatContractId } from "$lib/store/chat/chat.store";
  import { onMount } from "svelte";

  const features = [
    {
      icon: AnnotationOutline,
      title: "Real-Time Messaging",
      description: "Instant communication with peers and team members",
    },
    {
      icon: FileCloneOutline,
      title: "Contract Integration",
      description: "Seamlessly share and discuss contract details within chats",
    },
    {
      icon: LockOutline,
      title: "Secure Conversations",
      description:
        "End-to-end encryption for all messages and shared documents",
    },
    {
      icon: UsersGroupOutline,
      title: "Group Chats",
      description:
        "Create topic-specific group conversations for team collaboration",
    },
    {
      icon: GlobeOutline,
      title: "Language Translation",
      description:
        "Built-in translation for smooth international communication",
    },
    {
      icon: CogOutline,
      title: "Customizable Notifications",
      description: "Set alerts for high-priority messages and updates",
    },
  ];

  const mockConversation = [
    {
      user: "Alice",
      message:
        "Hey Bob, can you check the latest terms for the iron ore shipment?",
      time: "10:30 AM",
    },
    {
      user: "Bob",
      message:
        "Sure, I'm looking at it now. The delivery date has been pushed back by a week.",
      time: "10:32 AM",
    },
    {
      user: "Alice",
      message:
        "That might affect our scheduling. Can you share the updated contract details?",
      time: "10:33 AM",
    },
    {
      user: "System",
      message: "Bob has shared Contract #IR078 - Iron Ore Shipment",
      time: "10:34 AM",
      isSystem: true,
    },
    {
      user: "Bob",
      message:
        "I've just shared the latest version. Let me know if you need anything else.",
      time: "10:34 AM",
    },
  ];
  // eslint-disable-next-line no-undef
  onMount(() => {
    $currentChatContractId = "";
  });
</script>

<Chat conversationTitle="Ask AI anything" useTools="true" />
<!--
<Card class="w-full mx-auto max-w-full p-4">
	<h2 class="text-3xl font-bold mb-4 flex items-center">
		<AnnotationOutline class="w-8 h-8 mr-2 text-blue-500" />
		Smart Chat Module
	</h2>

	<p class="text-lg mb-6">
		Elevate your team communication with our integrated Smart Chat Module.
		Seamlessly discuss deals, share contract details, and collaborate in
		real-time, all within your trading platform.
	</p>

	<div class="grid md:grid-cols-2 gap-6 mb-8">
		{#each features as feature}
			<div class="flex items-start">
				<div class="flex-shrink-0 mr-3">
					<svelte:component this={feature.icon} class="w-6 h-6 text-blue-500" />
				</div>
				<div>
					<h3 class="text-lg font-semibold mb-1">{feature.title}</h3>
					<p>{feature.description}</p>
				</div>
			</div>
		{/each}
	</div>

	<div class="mb-8 border rounded-lg p-4 bg-gray-50 dark:bg-gray-800">
		<h3 class="text-xl font-semibold mb-4">Live Chat Preview</h3>
		<div class="space-y-4">
			{#each mockConversation as message}
				<div class="flex items-start">
					<Avatar class="mr-3" />
					<div
						class="bg-white rounded-lg p-3 shadow-sm flex-grow dark:bg-gray-700"
					>
						<div class="flex justify-between items-center mb-1">
							<span class="font-semibold">{message.user}</span>
							<span class="text-xs text-gray-500">{message.time}</span>
						</div>
						<p class={message.isSystem ? "text-sm text-blue-600" : "text-sm"}>
							{#if message.isSystem}
								<ShareAllOutline class="w-4 h-4 inline mr-1" />
							{/if}
							{message.message}
						</p>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<div class="mb-8">
		<h3 class="text-xl font-semibold mb-4">Additional Features</h3>
		<ul class="list-disc pl-5 space-y-2">
			<li>Intelligent contract parsing and summary generation</li>
			<li>Automated tagging and categorization of conversations</li>
			<li>
				Integration with calendar for scheduling meetings directly from chat
			</li>
			<li>Voice and video call capabilities for in-depth discussions</li>
			<li>Searchable message and file history for easy reference</li>
			<li>Compliance-friendly chat archiving and auditing tools</li>
		</ul>
	</div>

	<div class="flex justify-center space-x-4">
		<Button
			size="xl"
			color="blue"
			class="bg-theme-primary duration-300 duration-300 hover:bg-theme-secondary dark:bg-theme-secondary dark:hover:bg-theme-primary focus:ring-0 focus:outline-none"
		>
			<PhoneOutline class="w-5 h-5 mr-2" />
			Start Chatting Now
		</Button>
		<Button size="xl" color="alternative" class="hover:text-theme-primary"
			>Request Demo</Button
		>
	</div>
</Card>
-->
