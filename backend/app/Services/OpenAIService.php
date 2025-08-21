<?php

namespace App\Services;

use Illuminate\Support\Str;

class OpenAIService
{
    private string $apiKey;
    private $client = null;

    public function __construct()
    {
        $this->apiKey = (string) env('OPENAI_API_KEY', '');
        if ($this->apiKey && class_exists('OpenAI\\Client') && class_exists('OpenAI')) {
            // openai-php/client style
            $this->client = \OpenAI::client($this->apiKey);
        }
    }

    public function available(): bool
    {
        return !empty($this->apiKey);
    }

    public function generateAnswer(string $prompt, ?int $personaId = null, ?string $systemOverride = null, ?string $modelOverride = null): string
    {
        if (!$this->available()) {
            return '[OpenAI key missing]';
        }

        $system = $systemOverride ?: 'You are a concise, expert assistant. Answer in the user\'s saved style/persona if provided. Prefer short, high-signal responses.';

        // Select model (UI override > env > default)
        $modelToUse = (function() use ($modelOverride) {
            return $modelOverride ?: (string) env('OPENAI_MODEL', 'gpt-4o-mini');
        })();

        // Prefer library if installed
        if ($this->client) {
            try {
                $response = $this->client->chat()->create([
                    'model' => $modelToUse,
                    'temperature' => 0.4,
                    'messages' => [
                        ['role' => 'system', 'content' => $system],
                        ['role' => 'user', 'content' => $prompt],
                    ],
                ]);
                $choice = $response->choices[0] ?? null;
                if ($choice && isset($choice->message->content)) {
                    return trim((string) $choice->message->content);
                }
            } catch (\Throwable $e) {
                // fall through to HTTP client
            }
        }

        // Fallback: direct HTTP call to OpenAI Chat Completions
        $payload = [
            'model' => $modelToUse,
            'temperature' => 0.4,
            'messages' => [
                ['role' => 'system', 'content' => $system],
                ['role' => 'user', 'content' => $prompt],
            ],
        ];

        $ch = curl_init('https://api.openai.com/v1/chat/completions');
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => [
                'Authorization: Bearer ' . $this->apiKey,
                'Content-Type: application/json',
            ],
            CURLOPT_POSTFIELDS => json_encode($payload),
            CURLOPT_TIMEOUT => 60,
        ]);
        $raw = curl_exec($ch);
        if ($raw === false) {
            curl_close($ch);
            return '[OpenAI request failed]';
        }
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        $data = json_decode($raw, true);
        if ($code >= 200 && $code < 300 && isset($data['choices'][0]['message']['content'])) {
            return trim((string) $data['choices'][0]['message']['content']);
        }
        return '[OpenAI error]';
    }
}

