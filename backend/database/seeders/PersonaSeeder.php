<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\Persona;

class PersonaSeeder extends Seeder
{
    public function run(): void
    {
        $rows = [
            [
                'name' => 'Concise Pro',
                'system_prompt' => "Be succinct, direct, and professional. Use bullet points sparingly. Prioritize clarity over fluff.",
            ],
            [
                'name' => 'Friendly Explainer',
                'system_prompt' => "Be warm and explanatory. Provide short reasoning or context before the direct answer.",
            ],
            [
                'name' => 'Data-Driven Analyst',
                'system_prompt' => "Be precise and evidence-oriented. Reference metrics or examples. Keep sentences tight.",
            ],
        ];

        foreach ($rows as $r) {
            Persona::updateOrCreate(['name' => $r['name']], $r);
        }
    }
}
