<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class TranscriptChunk extends Model
{
    use HasFactory;

    protected $fillable = [
        'session_id', 'text', 'source',
    ];
}
