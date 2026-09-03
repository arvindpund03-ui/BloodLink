def donor_list(request):
    donors = UserProfile.objects.all()

    blood_group = request.GET.get("blood_group", "").strip()
    city = request.GET.get("city", "").strip()
    available = request.GET.get("available", "").strip()

    if blood_group:
        donors = donors.filter(blood_group__iexact=blood_group)

    if city:
        donors = donors.filter(city__icontains=city)

    if available == "1":
        donors = donors.filter(is_available=True)

    donors = donors.order_by("-id")

    return render(request, "donor_list.html", {
        "donors": donors,
        "selected_blood_group": blood_group,
        "selected_city": city,
        "available_only": available == "1",
    })