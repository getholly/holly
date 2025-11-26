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
  <title>Privacy Policy - Holly</title>
  <meta
    name="description"
    content="Privacy Policy for Holly - AI-powered code amendment platform"
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
            Privacy Policy
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
              This comprehensive privacy policy applies to Holly, an AI-powered
              code amendment platform that analyzes GitHub repositories and uses
              multiple Large Language Models (LLMs) and AI agents to improve and
              modify code. We are committed to transparency and protecting your
              privacy.
            </p>
          </div>

          <p class="text-sm text-gray-500 dark:text-gray-400">
            Last updated: {new Date().toLocaleDateString()}
          </p>

          <div class="space-y-8">
            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                1. About Holly and Data Collection
              </h2>
              <p>
                Holly is developed and operated by TeCharge Ltd, a UK-based
                technology company specializing in AI-powered development tools.
                We collect and process data necessary to provide our AI-powered
                code analysis services, including account information,
                repository data you authorize us to access, AI analysis results,
                and technical usage information.
              </p>
              <p>
                We implement strict data minimization principles, collecting
                only the information necessary to deliver our services
                effectively. All data processing is governed by applicable
                privacy laws including GDPR, UK GDPR, and CCPA.
              </p>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                2. How We Use Your Information
              </h2>
              <p>
                Your information is primarily used to provide Holly's AI-powered
                code analysis services. This includes processing your code
                through multiple LLMs and AI agents, generating improvement
                suggestions, providing repository insights, and maintaining
                platform security and performance.
              </p>
              <ul class="list-disc list-inside ml-4 space-y-2">
                <li>
                  <strong>Core Service Delivery:</strong> AI-powered code analysis,
                  improvement suggestions, and repository insights
                </li>
                <li>
                  <strong>Platform Operations:</strong> Account management, customer
                  support, system monitoring, and security
                </li>
                <li>
                  <strong>Service Improvement:</strong> Enhancing AI models and platform
                  features using aggregated, anonymized data
                </li>
                <li>
                  <strong>Communication:</strong> Service updates, security alerts,
                  and customer support
                </li>
              </ul>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                3. AI Processing and Code Security
              </h2>
              <p>
                Holly employs sophisticated AI infrastructure with multiple
                Large Language Models and specialized AI agents. Your code is
                processed in secure, isolated environments with strict access
                controls and temporary retention only.
              </p>
              <div
                class="border border-yellow-200 dark:border-yellow-800 rounded-lg p-4"
              >
                <h4
                  class="text-base font-medium text-yellow-800 dark:text-yellow-200 mb-2"
                >
                  Important AI Processing Notes:
                </h4>
                <ul
                  class="text-sm text-yellow-700 dark:text-yellow-300 list-disc list-inside space-y-1"
                >
                  <li>
                    Your specific code is never used to train our AI models
                    without explicit consent
                  </li>
                  <li>
                    Code processing occurs in isolated, ephemeral environments
                  </li>
                  <li>
                    AI suggestions are provided "as is" and should be reviewed
                    before implementation
                  </li>
                  <li>
                    Only aggregated, anonymized patterns are used for model
                    improvement
                  </li>
                </ul>
              </div>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                4. Data Security and Protection
              </h2>
              <p>
                We implement comprehensive security measures to protect your
                data:
              </p>
              <ul class="list-disc list-inside ml-4 space-y-2">
                <li>
                  <strong>Encryption:</strong> TLS 1.3 in transit, AES-256 at rest
                  with secure key management
                </li>
                <li>
                  <strong>Access Controls:</strong> Multi-factor authentication,
                  role-based access, and audit trails
                </li>
                <li>
                  <strong>Infrastructure:</strong> SOC 2 Type II certified cloud
                  providers with geographic controls
                </li>
                <li>
                  <strong>Monitoring:</strong> 24/7 security monitoring and automated
                  threat detection
                </li>
                <li>
                  <strong>Code Protection:</strong> Isolated processing environments
                  with no persistent storage
                </li>
              </ul>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                5. Data Sharing and Third Parties
              </h2>
              <p>
                We work with trusted AI service providers and cloud platforms
                under strict data protection agreements. We integrate with
                GitHub through official APIs and only access repositories you
                explicitly authorize.
              </p>
              <div
                class="border border-red-200 dark:border-red-800 rounded-lg p-4"
              >
                <p class="text-red-800 dark:text-red-200 font-semibold">
                  <strong>Our Commitment:</strong> We do not sell, rent, or trade
                  your personal information or code data to third parties for marketing
                  or commercial purposes. Your data is not a product.
                </p>
              </div>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                6. Data Retention and Deletion
              </h2>
              <p>
                We retain data only as long as necessary for service provision
                and legal compliance:
              </p>
              <ul class="list-disc list-inside ml-4 space-y-2">
                <li>
                  <strong>Active Account Data:</strong> Retained while your account
                  is active
                </li>
                <li>
                  <strong>Code Analysis Data:</strong> Deleted within 30 days of
                  analysis completion
                </li>
                <li>
                  <strong>Account Deletion:</strong> All personal data deleted within
                  90 days of account closure
                </li>
                <li>
                  <strong>Backup Systems:</strong> Data removed from backups within
                  1 year
                </li>
              </ul>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                7. Your Rights and Control
              </h2>
              <p>
                You have comprehensive control over your data and repository
                access:
              </p>
              <ul class="list-disc list-inside ml-4 space-y-2">
                <li>
                  <strong>Repository Control:</strong> Choose which repositories
                  to connect and revoke access anytime
                </li>
                <li>
                  <strong>Data Rights:</strong> Access, correct, delete, or export
                  your personal data (GDPR/CCPA compliant)
                </li>
                <li>
                  <strong>Privacy Settings:</strong> Control data sharing and analytics
                  participation
                </li>
                <li>
                  <strong>Account Management:</strong> Full control over account
                  settings and preferences
                </li>
              </ul>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                8. International Operations
              </h2>
              <p>
                Holly operates globally with appropriate safeguards for
                international data transfers. We use Standard Contractual
                Clauses (SCCs) and ensure compliance with local data protection
                laws.
              </p>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                9. Updates to This Policy
              </h2>
              <p>
                We may update this privacy policy to reflect changes in our
                practices or legal requirements. Material changes will be
                communicated via email and platform notifications with advance
                notice.
              </p>
            </div>

            <div class="space-y-4">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                10. Contact Information
              </h2>
              <p>
                For privacy questions or to exercise your rights, contact us:
              </p>
              <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 ml-4">
                <p><strong>TeCharge Ltd</strong></p>
                <p><strong>Privacy Contact:</strong> privacy@techarge.co.uk</p>
                <p>
                  <strong>Data Protection Officer:</strong> dpo@techarge.co.uk
                </p>
                <p><strong>Support:</strong> support@techarge.co.uk</p>
                <p><strong>Website:</strong> https://techarge.co.uk</p>
                <p>
                  <strong>Response Time:</strong> 48 hours for privacy inquiries
                </p>
              </div>
            </div>

            <div
              class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mt-6"
            >
              <h3
                class="text-lg font-medium text-blue-800 dark:text-blue-200 mb-3"
              >
                Quick Summary
              </h3>
              <ul
                class="text-sm text-blue-700 dark:text-blue-300 list-disc list-inside space-y-1"
              >
                <li>
                  <strong>Data Use:</strong> We use your data solely to provide AI-powered
                  code analysis services
                </li>
                <li>
                  <strong>Code Security:</strong> Your code is processed securely
                  in isolated environments
                </li>
                <li>
                  <strong>No Sales:</strong> We never sell your personal information
                  or code to third parties
                </li>
                <li>
                  <strong>Your Control:</strong> You control which repositories we
                  access and can revoke access anytime
                </li>
                <li>
                  <strong>Global Compliance:</strong> We comply with GDPR, CCPA,
                  and international privacy laws
                </li>
                <li>
                  <strong>Contact:</strong> Reach us at privacy@techarge.co.uk for
                  any privacy questions
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
