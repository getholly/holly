<script lang="ts">
  import { selectedTheme } from "$lib/store/theme.store";
  import { Button } from "flowbite-svelte";
  import { goto } from "$app/navigation";
  import { routes } from "$lib/routes";

  function goBack() {
    goto(routes.register?.path || "/register");
  }
</script>

<svelte:head>
  <title>Terms and Conditions - Holly</title>
  <meta
    name="description"
    content="Terms and Conditions for Holly - AI-powered code amendment platform"
  />
</svelte:head>

<section
  class="{$selectedTheme.authBackgroundClass} flex flex-col bg-theme-light-bg dark:bg-theme-dark-bg bg-opacity-60 bg-cover bg-center bg-no-repeat bg-blend-multiply h-full overflow-y-scroll py-6"
>
  <div class="pt:mt-0 mx-auto flex flex-col items-center justify-center w-full">
    <div
      class="w-full max-w-7xl rounded-lg bg-white shadow dark:bg-gray-900 md:mt-0 xl:p-0"
    >
      <div class="p-4">
        <div class="flex items-center justify-between mb-6">
          <h1
            class="text-2xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-3xl"
          >
            Terms and Conditions
          </h1>
        </div>

        <div class="text-gray-700 dark:text-gray-300 space-y-6">
          <div
            class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6"
          >
            <div class="flex items-center mb-2">
              <div class="text-blue-600 dark:text-blue-400 font-semibold">
                Holly by TeCharge
              </div>
            </div>
            <p class="text-sm text-blue-700 dark:text-blue-300">
              These terms and conditions apply to Holly, an AI-powered code
              amendment platform that analyzes GitHub repositories and uses
              multiple Large Language Models (LLMs) and AI agents to improve and
              modify code.
            </p>
          </div>

          <p class="text-sm text-gray-500 dark:text-gray-400">
            Last updated: {new Date().toLocaleDateString()}
          </p>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              1. Acceptance of Terms
            </h2>
            <p>
              By accessing and using Holly, operated by TeCharge.co.uk, you
              accept and agree to be bound by these terms and conditions. If you
              do not agree to abide by these terms, please do not use our
              AI-powered code amendment service.
            </p>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              2. Service Description
            </h2>
            <p>
              Holly is an AI-powered platform that connects to your GitHub
              repositories and uses multiple Large Language Models (LLMs) and AI
              agents to analyze, understand, and suggest improvements to your
              code. Our service includes:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>Automated code analysis and improvement suggestions</li>
              <li>AI-powered bug detection and fixing recommendations</li>
              <li>Code optimization and refactoring suggestions</li>
              <li>Repository insights and analysis reports</li>
              <li>Integration with GitHub through official APIs</li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              3. Account Registration and GitHub Integration
            </h2>
            <p>
              To use Holly, you must create an account and connect your GitHub
              account through OAuth. You are responsible for:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>Providing accurate and complete registration information</li>
              <li>Maintaining the security of your account credentials</li>
              <li>Managing which repositories you grant access to</li>
              <li>All activities that occur under your account</li>
              <li>
                Ensuring you have the right to grant access to repositories you
                connect
              </li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              4. Acceptable Use
            </h2>
            <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
              4.1 Permitted Uses
            </h3>
            <p>You may use Holly to:</p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>Analyze and improve your own code repositories</li>
              <li>Generate AI-powered suggestions for code optimization</li>
              <li>Receive automated recommendations for bug fixes</li>
              <li>Access insights about code quality and structure</li>
            </ul>

            <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
              4.2 Prohibited Uses
            </h3>
            <p>You may not use Holly to:</p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>
                Process repositories you do not own or have permission to access
              </li>
              <li>Generate malicious code or security exploits</li>
              <li>Attempt to reverse engineer our AI models or algorithms</li>
              <li>Overload our systems with excessive requests</li>
              <li>Violate any applicable laws or regulations</li>
              <li>Infringe upon intellectual property rights of others</li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              5. AI-Generated Content and Suggestions
            </h2>
            <p>
              <strong>No Warranty:</strong> AI-generated code suggestions, improvements,
              and analysis are provided "as is" without warranty. You acknowledge
              that:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>
                AI suggestions may contain errors or may not be optimal for your
                specific use case
              </li>
              <li>
                You are responsible for reviewing, testing, and validating all
                AI-generated content
              </li>
              <li>
                We do not guarantee the accuracy, completeness, or functionality
                of suggestions
              </li>
              <li>
                AI models may have limitations and biases inherent to their
                training data
              </li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              6. Intellectual Property
            </h2>
            <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
              6.1 Your Code
            </h3>
            <p>
              You retain all rights to your original code. By using Holly, you
              grant us a limited license to:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>Process your code through our AI systems for analysis</li>
              <li>Generate suggestions and improvements based on your code</li>
              <li>Store temporary copies necessary for service operation</li>
            </ul>

            <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
              6.2 AI-Generated Content
            </h3>
            <p>
              AI-generated suggestions and improvements become part of your
              codebase when you choose to implement them. However, similar
              suggestions may be generated for other users with similar code
              patterns.
            </p>

            <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
              6.3 Our Platform
            </h3>
            <p>
              Holly's technology, algorithms, and AI models remain our exclusive
              property and are protected by intellectual property laws.
            </p>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              7. Data Security and Privacy
            </h2>
            <p>
              We implement industry-standard security measures to protect your
              code and data. However, you acknowledge that:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>
                No system is completely secure, and we cannot guarantee absolute
                security
              </li>
              <li>
                You should avoid processing repositories with highly sensitive
                credentials or secrets
              </li>
              <li>
                Our Privacy Policy governs how we collect, use, and protect your
                data
              </li>
              <li>
                Code processing may involve third-party AI service providers
                with appropriate safeguards
              </li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              8. Limitation of Liability
            </h2>
            <p>
              To the maximum extent permitted by law, TeCharge.co.uk and Holly
              shall not be liable for:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>
                Any direct, indirect, incidental, special, or consequential
                damages
              </li>
              <li>Loss of profits, data, or business opportunities</li>
              <li>
                Damages resulting from AI-generated suggestions or code
                modifications
              </li>
              <li>System downtime or service interruptions</li>
              <li>Security breaches beyond our reasonable control</li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              9. Service Availability and Modifications
            </h2>
            <p>
              We strive to provide reliable service but reserve the right to:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>
                Modify, suspend, or discontinue features with reasonable notice
              </li>
              <li>
                Perform maintenance that may temporarily affect availability
              </li>
              <li>
                Update our AI models and algorithms to improve service quality
              </li>
              <li>
                Implement usage limits to ensure fair access for all users
              </li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              10. Termination
            </h2>
            <p>
              Either party may terminate this agreement at any time. Upon
              termination:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>Your access to Holly will cease immediately</li>
              <li>
                We will delete your account data in accordance with our Privacy
                Policy
              </li>
              <li>
                You may export your data before termination using available
                tools
              </li>
              <li>
                Surviving provisions (intellectual property, limitation of
                liability) remain in effect
              </li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              11. Governing Law and Disputes
            </h2>
            <p>
              These terms are governed by the laws of the United Kingdom. Any
              disputes will be resolved through:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>Good faith negotiation as the first step</li>
              <li>Mediation if negotiation fails</li>
              <li>Binding arbitration or UK courts as appropriate</li>
            </ul>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              12. Changes to Terms
            </h2>
            <p>
              We may update these terms to reflect changes in our service or
              legal requirements. We will notify you of material changes
              through:
            </p>
            <ul class="list-disc list-inside ml-4 space-y-2">
              <li>Email notification to your registered address</li>
              <li>Prominent notice on our platform</li>
              <li>Updated effective date on these terms</li>
            </ul>
            <p>
              Continued use after changes constitutes acceptance of the updated
              terms.
            </p>
          </div>

          <div class="space-y-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              13. Contact Information
            </h2>
            <p>For questions about these terms or our service, contact us:</p>
            <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 ml-4">
              <p><strong>TeCharge Ltd</strong></p>
              <p>Email: legal@techarge.co.uk</p>
              <p>Support: support@techarge.co.uk</p>
              <p>Website: https://techarge.co.uk</p>
              <p>Address: United Kingdom</p>
            </div>
          </div>

          <div
            class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mt-6"
          >
            <h3
              class="text-lg font-medium text-blue-800 dark:text-blue-200 mb-2"
            >
              By using Holly, you acknowledge that:
            </h3>
            <ul
              class="text-sm text-blue-700 dark:text-blue-300 list-disc list-inside space-y-1"
            >
              <li>You have read, understood, and agree to these terms</li>
              <li>You understand the AI-powered nature of our service</li>
              <li>
                You will use the service responsibly and in accordance with
                these terms
              </li>
              <li>
                You accept the risks and limitations associated with
                AI-generated content
              </li>
            </ul>
          </div>
        </div>

        <div class="pt-6 border-t border-gray-200 dark:border-gray-700">
          <Button
            on:click={goBack}
            class="w-full bg-theme-primary hover:bg-theme-primary-dark focus:outline-none focus:ring-0 dark:bg-theme-primary dark:hover:bg-theme-primary-dark"
          >
            Back to Registration
          </Button>
        </div>
      </div>
    </div>
  </div>
</section>
