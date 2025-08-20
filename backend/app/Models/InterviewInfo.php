<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class InterviewInfo extends Model
{
    use HasFactory;

    protected $fillable = [
        'session_id', 'company', 'role', 'context',
    ];
}
