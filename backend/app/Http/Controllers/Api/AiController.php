<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use App\Services\OpenAIService;
use App\Models\Persona;
use App\Models\TranscriptChunk;
use App\Models\QAEntry;
use App\Models\InterviewInfo;

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
            'session_id' => ['nullable', 'string', 'max:100'],
            'model' => ['nullable', 'string', 'max:50'],
        ]);

        $baseSystem = "You are a concise, expert assistant. Prefer short, high-signal responses.";
        $system = $baseSystem;

        // Persona enrichment
        $personaId = $validated['persona_id'] ?? null;
        $persona = null;
        if ($personaId) {
            $persona = Persona::find($personaId);
            if ($persona) {
                $system .= "\n\nPersona instructions:\n" . $persona->system_prompt;
            }
        }

        // Interview info enrichment
        $sid = $validated['session_id'] ?? null;
        if ($sid) {
            $info = InterviewInfo::where('session_id', $sid)->first();
            if ($info) {
                $system .= "\n\nInterview context:";
                if ($info->company) { $system .= "\nCompany: {$info->company}"; }
                if ($info->role) { $system .= "\nRole: {$info->role}"; }
                if ($info->context) {
                    $limit = (int) env('INTERVIEW_NOTES_SOFT_LIMIT', 10000);
                    $notes = (string) $info->context;
                    if (strlen($notes) > $limit) {
                        $headLen = (int) floor($limit * 0.7);
                        $tailLen = (int) floor($limit * 0.25);
                        $head = substr($notes, 0, $headLen);
                        $tail = substr($notes, -$tailLen);
                        $notes = $head . "\n[... truncated for speed/context ...]\n" . $tail;
                    }
                    $system .= "\nNotes:\n{$notes}";
                }
            }
        }

        $model = isset($validated['model']) ? (string) $validated['model'] : null;
        $answer = $openai->generateAnswer($validated['prompt'], null, $system, $model);

        // Persist QA entry
        QAEntry::create([
            'session_id' => $sid ?? 'local-dev',
            'persona_id' => $persona?->id,
            'question' => $validated['prompt'],
            'ai_answer' => $answer,
        ]);

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

        TranscriptChunk::create([
            'session_id' => $validated['session_id'] ?? 'local-dev',
            'text' => $validated['text'],
            'source' => $validated['source'] ?? null,
        ]);

        return response()->json(['ok' => true]);
    }

    public function personas(): JsonResponse
    {
        $rows = Persona::query()->select(['id', 'name', 'description', 'system_prompt'])->orderBy('id')->get();
        return response()->json(['personas' => $rows]);
    }

    public function upsertInterviewInfo(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'session_id' => ['required', 'string', 'max:100'],
            'company' => ['nullable', 'string', 'max:150'],
            'role' => ['nullable', 'string', 'max:150'],
            'context' => ['nullable', 'string'],
        ]);

        $info = InterviewInfo::updateOrCreate(
            ['session_id' => $validated['session_id']],
            [
                'company' => $validated['company'] ?? null,
                'role' => $validated['role'] ?? null,
                'context' => $validated['context'] ?? null,
            ]
        );

        return response()->json(['ok' => true, 'interview_info' => $info]);
    }

    public function getInterviewInfo(Request $request): JsonResponse
    {
        $sid = (string) $request->query('session_id', 'local-dev');
        $info = InterviewInfo::where('session_id', $sid)->first();
        return response()->json(['interview_info' => $info]);
    }
}

