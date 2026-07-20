import type { Dictionary } from './en'

/**
 * Terms marked (epoint) come from the production dashboard. The rest were
 * translated for the sandbox and want a native speaker's review.
 */
export const az: Dictionary = {
  nav: {
    transactions: 'Əməliyyatlar',
    balance: 'Balans', // epoint
    cards: 'Kartlar / Hesablar', // epoint
    invoices: 'Link ilə Ödəniş', // epoint
    bankTransfers: 'Bank köçürmələri',
    apiManagement: 'API Idarəetmə', // epoint
    sandboxTools: 'Sandbox alətləri',
    callbacks: 'Geri çağırışlar',
    requestLog: 'Sorğu loqları',
    testCards: 'Test kartları',
    signatureTool: 'İmza aləti',
    menu: 'Menyu',
  },
  common: {
    loading: 'Yüklənir…',
    apiUnreachable: 'Sandbox API-yə qoşulmaq mümkün olmadı.',
    apiUnreachableHint: 'API-nin 8181 portunda işlədiyini yoxlayın.',
    noData: 'Seçilmiş dövr üzrə məlumat tapılmadı.', // epoint
    total: 'Cəmi', // epoint
    copy: 'Kopyala',
    copied: 'Kopyalandı',
    show: 'Göstər',
    hide: 'Gizlət',
    inspect: 'Bax',
    notSet: 'təyin edilməyib',
    expandRow: 'Sətri aç',
    collapseRow: 'Sətri bağla',
    edit: 'Redaktə et',
    save: 'Yadda saxla',
    saving: 'Saxlanılır…',
    cancel: 'Ləğv et',
    apiReference: 'API sənədləri',
  },
  transactions: {
    title: 'Əməliyyatlar',
    empty: 'Hələ əməliyyat yoxdur. POST /api/1/request ilə yaradın.',
    transaction: 'Əməliyyat', // epoint
    orderId: 'Sifariş ID',
    status: 'Status',
    sum: 'Məbləğ', // epoint
    bankCode: 'Bank kodu',
    card: 'Kart', // epoint
    rrn: 'RRN', // epoint
    endpoint: 'Endpoint',
    description: 'Təsvir', // epoint
    traceId: 'Trace ID',
    date: 'Tarix', // epoint
  },
  callbacks: {
    title: 'Geri çağırışlar',
    empty: 'Hələ geri çağırış göndərilməyib.',
    emptyHint: 'API Idarəetmə səhifəsində result_url təyin edin, sonra ödənişi tamamlayın.',
    attempt: 'cəhd',
    noResponse: 'cavab yoxdur',
    decodedPayload: 'Açılmış məlumat',
    rawData: 'data (base64)',
    signature: 'imza',
    yourResponse: 'Sizin cavabınız',
    error: 'Xəta',
  },
  requestLog: {
    title: 'Sorğu loqları',
    empty: 'Hələ API sorğusu qeydə alınmayıb.',
    method: 'Metod',
    path: 'Yol',
    status: 'Status',
    signature: 'İmza',
    valid: 'düzgün',
    invalid: 'yanlış',
    time: 'Vaxt',
    request: 'Sorğu',
    response: 'Cavab', // epoint uses "Bank cavabı"
  },
  apiManagement: {
    title: 'API Idarəetmə', // epoint
    publicKey: 'Açıq açar',
    privateKey: 'Gizli açar',
    websiteAddress: 'Veb sayt ünvanı', // epoint
    successLink: 'Uğurlu keçid', // epoint
    failedLink: 'Uğursuz keçid', // epoint
    resultLink: 'Nəticənin göndəriləcəyi keçid', // epoint
    connectionOptions: 'Qoşulma parametrləri',
    accessEnabled: 'API girişi aktivdir.',
    rotateKey: 'Yeni gizli açar ver',
    rotateNote: 'Mövcud imzalar etibarsız olur, produksiyada olduğu kimi.',
    pointHere: 'İnteqrasiyanı buraya yönləndirin',
    pointHereBody:
      'Yalnız baza URL-i dəyişin, qalan hər şey eyni qalır. /api/1/ altındakı bütün yollar produksiya ilə üst-üstə düşür.',
    callbackNote:
      'Geri çağırışlar konteynerin daxilindən göndərilir. result_url üçün localhost əvəzinə http://host.docker.internal:PORT istifadə edin.',
  },
  testCards: {
    title: 'Test kartları',
    intro: 'epoint test kartları dərc etmir, ona görə sandbox öz kartlarını təyin edir.',
    outro: 'Kartın nömrəsi nəticəni göstərir.',
    cardNumber: 'Kartın nömrəsi', // epoint
    bankCode: 'Bank kodu',
    outcome: 'Nəticə',
    result: 'Status',
    approved: 'təsdiqləndi',
    declined: 'imtina edildi',
  },
  signature: {
    title: 'İmza aləti',
    intro: 'epoint sorğuları bu düsturla imzalayır:',
    introAfter:
      'SHA-1 nəticəsi hex sətri deyil, xam 20 bayt olmalıdır. Aşağıya işləməyən cütü yapışdırın, alət dəqiq səhvi göstərəcək.',
    verifyTitle: 'İmzanı yoxla',
    buildTitle: 'İmzalanmış sorğu yarat',
    privateKey: 'Gizli açar',
    data: 'data (base64)',
    signature: 'imza',
    check: 'Yoxla',
    sign: 'İmzala',
    payload: 'Məlumat (JSON)',
    matches: 'İmza uyğundur.',
    noMatch: 'İmza uyğun deyil.',
    invalidJson: 'Məlumat düzgün JSON deyil.',
    formula: 'Düstur',
    hashedString: 'Hash edilən sətir',
    expected: 'Gözlənilən imza',
    decoded: 'Açılmış məlumat',
    readyToRun: 'İşə salmağa hazır',
  },
  planned: {
    balanceTitle: 'Balans', // epoint
    balanceSummary: 'Balans hesabatı hələ hazır deyil.',
    cardsTitle: 'Kartlar / Hesablar', // epoint
    cardsSummary: 'Hələ qeydiyyatdan keçmiş kart yoxdur.',
    invoicesTitle: 'Link ilə Ödəniş', // epoint
    invoicesSummary: 'Hesab-fakturalar hələ hazır deyil.',
    backedBy: 'Bu endpointlərə əsaslanır:',
    notImplemented: 'hələ hazır deyil.',
  },
  balance: {
    title: 'Balans',
    empty: 'Hələ balans hərəkəti yoxdur.',
    emptyHint: 'Ödənişi tamamlayın, hesabat dolacaq.',
    current: 'Cari balans',
    entry: 'Qeyd',
    kind: 'Növ',
    amount: 'Məbləğ',
    runningTotal: 'Sonrakı balans',
    description: 'Təsvir',
    date: 'Tarix',
    kinds: {
      payment: 'Ödəniş',
      commission: 'Komissiya',
      split_in: 'Bölünmüş daxilolma',
      split_out: 'Bölünmüş çıxış',
      refund: 'Geri qaytarma',
      payout: 'Köçürmə',
      reversal: 'Ləğv',
    },
  },
  cards: {
    title: 'Kartlar / Hesablar',
    empty: 'Hələ qeydiyyatdan keçmiş kart yoxdur.',
    emptyHint: '/api/1/card-registration çağırın və yönləndirməni tamamlayın.',
    cardId: 'Kart ID',
    mask: 'Kartın nömrəsi',
    holder: 'Kart sahibi',
    expiry: 'Bitmə tarixi',
    status: 'Status',
    type: 'Növ',
    payout: 'Köçürmə kartı',
    payment: 'Ödəniş kartı',
    description: 'Təsvir',
    added: 'Əlavə edildi',
  },
  invoices: {
    title: 'Link ilə Ödəniş',
    empty: 'Hələ hesab-faktura yoxdur.',
    emptyHint: '/api/1/invoices/create ilə yaradın.',
    id: '#',
    total: 'Məbləğ',
    status: 'Status',
    recipient: 'Ad',
    description: 'Təsvir',
    contact: 'Əlaqə',
    period: 'Dövr',
    template: 'Şablon',
    created: 'Tarix',
    sent: 'Göndərilən mesajlar',
    sentEmpty: 'Hələ heç nə göndərilməyib.',
    channel: 'Kanal',
    recipientLabel: 'Alıcı',
    subject: 'Mövzu',
    body: 'Mesaj',
    statuses: {
      waiting_for_payment: 'Ödəniş gözlənilir',
      paid: 'Ödənilib',
      canceled: 'Ləğv edilib',
    },
  },
  b2b: {
    title: 'Bank köçürmələri',
    empty: 'Hələ bank köçürməsi yoxdur.',
    emptyHint: 'POST /api/1/b2b/payment ilə yaradın.',
    orderId: 'Sifariş ID',
    status: 'Status',
    amount: 'Məbləğ',
    payee: 'Alıcı',
    iban: 'IBAN',
    bankCode: 'Bank kodu',
    webhookSent: 'Webhook',
    bulkId: 'Bulk ID',
    created: 'Tarix',
    advance: 'İrəlilət',
    yes: 'göndərildi',
    no: 'göndərilməyib',
  },
  features: {
    title: 'Funksiyalar',
    intro:
      'epoint bunları hər merchant üçün ayrıca aktivləşdirir. Burada da söndürülüb ki, inteqrasiya produksiyadakı eyni imtina ilə qarşılaşsın.',
    amex_enabled: 'AMEX ödənişləri',
    token_payments_enabled: 'Apple Pay və Google Pay',
    installments_enabled: 'Taksitli ödənişlər',
    wallets_enabled: 'Pulqabı ödənişləri',
    b2b_enabled: 'B2B bank köçürmələri',
  },
  accounts: {
    title: 'Hesablar',
    intro:
      'Produksiyada bir merchant hesabınız olur. Sandbox bir neçəsini saxlamağa imkan verir ki, bölünmüş ödənişlərin real tərəf-müqabili olsun.',
    newName: 'Hesabın adı',
    create: 'Hesab yarat',
    select: 'Seç',
    remove: 'Sil',
    active: 'aktiv',
  },
  login: {
    title: 'Daxil olun',
    subtitle: 'Bu sandbox admin parolu ilə qorunur.',
    email: 'E-poçt',
    password: 'Parol',
    signIn: 'Daxil ol',
    signingIn: 'Daxil olunur…',
    failed: 'Daxil olmaq mümkün olmadı. Yenidən cəhd edin.',
    hint: 'Məlumatlar EPOINT_ADMIN_EMAIL və EPOINT_ADMIN_PASSWORD ilə təyin edilir.',
    signOut: 'Çıxış',
    openAccess: 'Qorunmayır',
    openAccessHint:
      'Bu sandbox-a çıxışı olan hər kəs açarlarınızı görə bilər. Giriş tələb etmək üçün EPOINT_ADMIN_EMAIL və EPOINT_ADMIN_PASSWORD təyin edin.',
  },
  footer: {
    sandbox: 'Sandbox',
    reference: 'Sənədlər',
    baseUrl: 'Baza URL',
    blurb:
      'epoint.az ödəniş şlüzü ilə inteqrasiya edən developerlər üçün lokal sandbox. Burada real ödəniş emal olunmur.',
    callbackNote:
      'Geri çağırışlar sizin kompüterinizə localhost deyil, host.docker.internal vasitəsilə çatır.',
    openapi: 'OpenAPI sxemi',
    developerPortal: 'Epoint developer portalı',
    legal: 'Epoint Sandbox. Epoint ilə əlaqəsi yoxdur. Yalnız lokal development üçün.',
  },
}
