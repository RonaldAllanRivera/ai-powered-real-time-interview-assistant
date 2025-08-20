<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class QAEntry extends Model
{
    use HasFactory;

    protected $table = 'qa_entries';

    protected $fillable = [
        'session_id', 'persona_id', 'question', 'ai_answer', 'final_answer',
    ];
}
