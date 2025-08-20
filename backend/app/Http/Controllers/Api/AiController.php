<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use App\Services\OpenAIService;

class AiController extends Controller
{
    public function health(): JsonResponse
    {
        return response()->json(['status' => 'ok']);
    }

    public function generate(Request $request, OpenAIService $openai): JsonResponse
    {
        $validated = $request->validate([
            'prompt' => ['required', 'string', 'max:20000'],
            'persona_id' => ['nullable', 'integer'],
        ]);

        $answer = $openai->generateAnswer($validated['prompt'], $validated['persona_id'] ?? null);

        // TODO: persist QA entry with session/persona association
        return response()->json([
            'answer' => $answer,
        ]);
    }

    public function storeTranscript(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'text' => ['required', 'string', 'max:20000'],
            'session_id' => ['nullable', 'string', 'max:100'],
            'source' => ['nullable', 'string', 'max:50'],
        ]);

        // TODO: persist transcript chunk. For now, just acknowledge.
        return response()->json([
            'ok' => true,
        ]);
    }
}
