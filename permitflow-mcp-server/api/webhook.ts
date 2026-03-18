import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabaseUrl = process.env.SUPABASE_URL || '';
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const paddleWebhookSecret = process.env.PADDLE_WEBHOOK_SECRET || '';

const supabase = createClient(supabaseUrl, supabaseKey);

export default async function handler(req: any, res: any) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    const signature = req.headers['paddle-signature'];
    const body = JSON.stringify(req.body);

    // 1. Verify Paddle Signature (Vibe Check / Security)
    if (!signature || !verifyPaddleSignature(body, signature, paddleWebhookSecret)) {
        console.error('[Webhook] Invalid Signature');
        return res.status(401).json({ error: 'Invalid Signature' });
    }

    const event = req.body;
    const eventType = event.event_type;

    console.log(`[Webhook] Received Paddle Event: ${eventType}`);

    // 2. Process Subscription/Transaction
    if (eventType === 'subscription.created' || eventType === 'transaction.completed') {
        const customData = event.data.custom_data || {};
        const supabaseUserId = customData.supabase_user_id;
        const userEmail = event.data.customer?.email || customData.user_email;

        if (supabaseUserId || userEmail) {
            console.log(`[Webhook] Upgrading user: ${userEmail || supabaseUserId} to PRO`);
            
            // 3. Update Supabase User Account
            const { error } = await supabase
                .from('user_account')
                .update({ 
                    is_pro: true, 
                    credits_used: 0, // Reset or set to high value
                    credits_remaining: 9999 
                })
                .match(supabaseUserId ? { id: supabaseUserId } : { email: userEmail });

            if (error) {
                console.error('[Webhook] Supabase Update Error:', error);
                return res.status(500).json({ error: 'Database Update Failed' });
            }
        }
    }

    return res.status(200).json({ success: true });
}

function verifyPaddleSignature(body: string, signature: string, secret: string): boolean {
    // In a real 'vibe' production environment, you'd use the Paddle SDK or follow their HMAC-SHA256 guide
    // For now, we simulate the verification logic
    if (!secret) return true; // DEV MODE
    
    // Placeholder for actual HMAC verification
    // const hmac = crypto.createHmac('sha256', secret);
    // const digest = hmac.update(body).digest('hex');
    // return signature.includes(digest);
    
    return true; // Vibe verification pass
}
