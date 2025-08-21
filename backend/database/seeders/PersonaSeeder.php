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
                'name' => 'Direct & Technical (Truthful)',
                'description' => "You explain exactly what you know and don't know.\nYou include relevant tools/tech you've worked with.\nExample: \"I haven't deployed production workflows in n8n, but I'm familiar with its structure and I've applied similar automation principles in Zapier and Make.com.\"",
                'system_prompt' => "Review my answer and make it direct, technical, and honest. Keep it concise, focus on my real experience, and mention alternatives if I haven't used the exact tool.",
            ],
            [
                'name' => 'Structured & Example-Driven',
                'description' => "You like to break your answers into bullet points or short sections.\nYou show credibility by citing specific projects or outcomes.\nExample: \"At LogicMedia, I lead full-stack web projects… At PulseIQ, I build custom WordPress sites and plugins…\"",
                'system_prompt' => "Review my answer and make it structured and example-driven. Organize into clear points, highlight my roles and responsibilities, and give one or two real project examples.",
            ],
            [
                'name' => 'Polished & Professional',
                'description' => "You wrap up answers with confidence and alignment to the role.\nThe tone is respectful, client-facing, and smooth.\nExample: \"I'm highly teachable, adapt quickly to new tools, and focus on delivering reliable, scalable solutions. I believe these qualities align well with your client-focused environment.\"",
                'system_prompt' => "Review my answer and make it polished and professional. Keep the tone confident, use complete sentences, and finish with how my skills align with the role or company values.",
            ],
        ];

        foreach ($rows as $r) {
            Persona::updateOrCreate(['name' => $r['name']], $r);
        }
    }
}
