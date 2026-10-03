/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include <sal/config.h>

#include <string_view>
#include <utility>

#include <vcl/builder.hxx>
#include <vcl/commandinfoprovider.hxx>
#include <vcl/layout.hxx>
#include <vcl/notebookbar/notebookbar.hxx>
#include <vcl/notebookbar/NotebookBarAddonsItem.hxx>
#include <vcl/syswin.hxx>
#include <vcl/tabctrl.hxx>
#include <vcl/taskpanelist.hxx>
#include <vcl/themecolors.hxx>
#include <vcl/NotebookbarContextControl.hxx>
#include <cppuhelper/implbase.hxx>
#include <comphelper/processfactory.hxx>
#include <officecfg/Office/Common.hxx>
#include <osl/file.hxx>
#include <config_folders.h>
#include <com/sun/star/frame/XFrame.hpp>
#include <com/sun/star/frame/FrameAction.hpp>
#include <com/sun/star/ui/ContextChangeEventMultiplexer.hpp>
#include <comphelper/lok.hxx>

/**
 * split from the main class since it needs different ref-counting mana
 */
class NotebookBarContextChangeEventListener : public ::cppu::WeakImplHelper<css::ui::XContextChangeEventListener, css::frame::XFrameActionListener>
{
    bool mbActive;
    VclPtr<NotebookBar> mpParent;
    css::uno::Reference<css::frame::XFrame> mxFrame;
public:
    NotebookBarContextChangeEventListener(NotebookBar *p, css::uno::Reference<css::frame::XFrame> xFrame) :
        mbActive(false),
        mpParent(p),
        mxFrame(std::move(xFrame))
    {}

    void setupFrameListener(bool bListen);
    void setupListener(bool bListen);

    // XContextChangeEventListener
    virtual void SAL_CALL notifyContextChangeEvent(const css::ui::ContextChangeEventObject& rEvent) override;

    // XFrameActionListener
    virtual void SAL_CALL frameAction(const css::frame::FrameActionEvent& rEvent) override;

    virtual void SAL_CALL disposing(const ::css::lang::EventObject&) override;
};

NotebookBar::NotebookBar(Window* pParent, const OUString& rID, const OUString& rUIXMLDescription,
                         const css::uno::Reference<css::frame::XFrame>& rFrame,
                         std::unique_ptr<NotebookBarAddonsItem> pNotebookBarAddonsItem)
    : Control(pParent)
    , m_pEventListener(new NotebookBarContextChangeEventListener(this, rFrame))
    , m_pViewShell(nullptr)
    , m_bIsWelded(false)
    , m_sUIXMLDescription(rUIXMLDescription)
    , m_sModule(vcl::CommandInfoProvider::GetModuleIdentifier(rFrame))
{
    m_pEventListener->setupFrameListener(true);

    SetStyle(GetStyle() | WB_DIALOGCONTROL);

    bool bIsWelded = comphelper::LibreOfficeKit::isActive();
    if (bIsWelded)
    {
        m_bIsWelded = true;
        m_xVclContentArea = VclPtr<VclVBox>::Create(this);
        m_xVclContentArea->Show();
        // now access it using GetMainContainer and set dispose callback with SetDisposeCallback
    }
    else
    {
        m_pUIBuilder.reset(
            new VclBuilder(this, AllSettings::GetUIRootDir(), rUIXMLDescription, rID, rFrame, true,
                           std::move(pNotebookBarAddonsItem)));

        // In the Notebookbar's .ui file must exist control handling context
        // - implementing NotebookbarContextControl interface with id "ContextContainer"
        // or "ContextContainerX" where X is a number >= 1
        NotebookbarContextControl* pContextContainer = nullptr;
        int i = 0;
        do
        {
            OUString aName = u"ContextContainer"_ustr;
            if (i)
                aName += OUString::number(i);

            pContextContainer = dynamic_cast<NotebookbarContextControl*>(m_pUIBuilder->get<Window>(aName));
            if (pContextContainer)
                m_pContextContainers.push_back(pContextContainer);
            i++;
        }
        while( pContextContainer != nullptr );
    }

    UpdateBackground();
}

NotebookBar::~NotebookBar()
{
    disposeOnce();
}

void NotebookBar::dispose()
{
    m_pContextContainers.clear();
    if (m_pSystemWindow && m_pSystemWindow->ImplIsInTaskPaneList(this))
        m_pSystemWindow->GetTaskPaneList()->RemoveWindow(this);
    m_pSystemWindow.reset();

    if (m_rDisposeLink.IsSet())
        m_rDisposeLink.Call(m_pViewShell);

    if (m_bIsWelded)
        m_xVclContentArea.disposeAndClear();
    else
        disposeBuilder();

    m_pEventListener->setupFrameListener(false);
    m_pEventListener->setupListener(false);
    m_pEventListener.clear();

    Control::dispose();
}

bool NotebookBar::PreNotify(NotifyEvent& rNEvt)
{
    // capture KeyEvents for taskpane cycling
    if (rNEvt.GetType() == NotifyEventType::KEYINPUT)
    {
        if (m_pSystemWindow)
            return m_pSystemWindow->PreNotify(rNEvt);
    }
    return Window::PreNotify( rNEvt );
}

Size NotebookBar::GetOptimalSize() const
{
    if (isLayoutEnabled(this))
        return VclContainer::getLayoutRequisition(*GetWindow(GetWindowType::FirstChild));

    return Control::GetOptimalSize();
}

void NotebookBar::setPosSizePixel(tools::Long nX, tools::Long nY, tools::Long nWidth, tools::Long nHeight, PosSizeFlags nFlags)
{
    bool bCanHandleSmallerWidth = false;
    bool bCanHandleSmallerHeight = false;

    bool bIsLayoutEnabled = isLayoutEnabled(this);
    Window *pChild = GetWindow(GetWindowType::FirstChild);

    if (bIsLayoutEnabled && pChild->GetType() == WindowType::SCROLLWINDOW)
    {
        WinBits nStyle = pChild->GetStyle();
        if (nStyle & (WB_AUTOHSCROLL | WB_HSCROLL))
            bCanHandleSmallerWidth = true;
        if (nStyle & (WB_AUTOVSCROLL | WB_VSCROLL))
            bCanHandleSmallerHeight = true;
    }

    Size aSize(GetOptimalSize());
    if (!bCanHandleSmallerWidth)
        nWidth = std::max(nWidth, aSize.Width());
    if (!bCanHandleSmallerHeight)
        nHeight = std::max(nHeight, aSize.Height());

    Control::setPosSizePixel(nX, nY, nWidth, nHeight, nFlags);

    if (bIsLayoutEnabled && (nFlags & PosSizeFlags::Size))
        VclContainer::setLayoutAllocation(*pChild, Point(0, 0), Size(nWidth, nHeight));
}

void NotebookBar::Resize()
{
    if(m_pUIBuilder && m_pUIBuilder->get_widget_root())
    {
        vcl::Window* pWindow = m_pUIBuilder->get_widget_root()->GetChild(0);
        if (pWindow)
        {
            Size aSize = pWindow->GetSizePixel();
            aSize.setWidth( GetSizePixel().Width() );
            pWindow->SetSizePixel(aSize);
        }
    }
    if(m_bIsWelded)
    {
        vcl::Window* pChild = GetWindow(GetWindowType::FirstChild);
        assert(pChild);
        VclContainer::setLayoutAllocation(*pChild, Point(0, 0), GetSizePixel());
        Control::Resize();
    }
    Control::Resize();
}

void NotebookBar::SetSystemWindow(SystemWindow* pSystemWindow)
{
    m_pSystemWindow = pSystemWindow;
    if (!m_pSystemWindow->ImplIsInTaskPaneList(this))
        m_pSystemWindow->GetTaskPaneList()->AddWindow(this);
}

void SAL_CALL NotebookBarContextChangeEventListener::notifyContextChangeEvent(const css::ui::ContextChangeEventObject& rEvent)
{
    if (mpParent)
    {
        for (NotebookbarContextControl* pControl : mpParent->m_pContextContainers)
            pControl->SetContext(vcl::EnumContext::GetContextEnum(rEvent.ContextName));
    }
}

void NotebookBarContextChangeEventListener::setupListener(bool bListen)
{
    if (comphelper::LibreOfficeKit::isActive())
        return;

    auto xMultiplexer(css::ui::ContextChangeEventMultiplexer::get(::comphelper::getProcessComponentContext()));

    if (bListen)
    {
        try
        {
            xMultiplexer->addContextChangeEventListener(this, mxFrame->getController());
        }
        catch (const css::uno::Exception&)
        {
        }
    }
    else
        xMultiplexer->removeAllContextChangeEventListeners(this);

    mbActive = bListen;
}

void NotebookBarContextChangeEventListener::setupFrameListener(bool bListen)
{
    if (bListen)
        mxFrame->addFrameActionListener(this);
    else
        mxFrame->removeFrameActionListener(this);
}

void SAL_CALL NotebookBarContextChangeEventListener::frameAction(const css::frame::FrameActionEvent& rEvent)
{
    if (!mbActive)
        return;

    if (rEvent.Action == css::frame::FrameAction_COMPONENT_REATTACHED)
    {
        setupListener(true);
    }
    else if (rEvent.Action == css::frame::FrameAction_COMPONENT_DETACHING)
    {
        setupListener(false);
        // We don't want to give up on listening; just wait for
        // another controller to be attached to the frame.
        mbActive = true;
    }
}

void NotebookBar::SetupListener(bool bListen)
{
    m_pEventListener->setupListener(bListen);
}

void SAL_CALL NotebookBarContextChangeEventListener::disposing(const ::css::lang::EventObject&)
{
    mpParent.reset();
}

void NotebookBar::DataChanged(const DataChangedEvent& rDCEvt)
{
    UpdateBackground();
    Control::DataChanged(rDCEvt);
}

void NotebookBar::StateChanged(const  StateChangedType nStateChange )
{
    UpdateBackground();
    Control::StateChanged(nStateChange);
    Invalidate();
}

void NotebookBar::UpdateBackground()
{
    // Arunika: flat ribbon like Microsoft Office 365 - white (or dark grey in dark mode) with the
    // application colour only on the active tab: Word blue, Excel green, PowerPoint orange
    const Color aDialog = GetSettings().GetStyleSettings().GetDialogColor();
    const bool bDark = aDialog.IsDark();
    Color aColor = bDark ? Color(0x29, 0x29, 0x29) : Color(0xff, 0xff, 0xff);

    Color aAccent(0x18, 0x5a, 0xbd);                                       // Word #185abd
    if (m_sModule == "com.sun.star.sheet.SpreadsheetDocument")
        aAccent = Color(0x10, 0x7c, 0x41);                                 // Excel #107c41
    else if (m_sModule == "com.sun.star.presentation.PresentationDocument")
        aAccent = Color(0xc4, 0x3e, 0x1c);                                 // PowerPoint #c43e1c
    else if (m_sModule == "com.sun.star.drawing.DrawingDocument")
        aAccent = Color(0x39, 0x55, 0xa3);                                 // Visio #3955a3

    for (NotebookbarContextControl* pControl : m_pContextContainers)
        if (auto pTabControl = dynamic_cast<NotebookbarTabControlBase*>(pControl))
            pTabControl->SetOfficeStyle(aAccent, aColor);

    SetBackground(Wallpaper(aColor));
    UpdateDefaultSettings();
    GetOutDev()->SetSettings( DefaultSettings );

    Invalidate(tools::Rectangle(Point(0,0), GetSizePixel()));
}

void NotebookBar::UpdateDefaultSettings()
{
    AllSettings aAllSettings( GetSettings() );
    StyleSettings aStyleSet( aAllSettings.GetStyleSettings() );

    ::Color aTextColor = aStyleSet.GetFieldTextColor();
    aStyleSet.SetDialogTextColor( aTextColor );
    aStyleSet.SetButtonTextColor( aTextColor );
    aStyleSet.SetRadioCheckTextColor( aTextColor );
    aStyleSet.SetGroupTextColor( aTextColor );
    aStyleSet.SetLabelTextColor( aTextColor );
    aStyleSet.SetWindowTextColor( aTextColor );
    aStyleSet.SetTabTextColor(aTextColor);
    aStyleSet.SetToolTextColor(aTextColor);
    // Arunika: group captions under the ribbon groups are grey, as in Office
    ::Color aCaption(aTextColor);
    aCaption.Merge(GetBackground().GetColor(), 150);
    aStyleSet.SetLabelTextColor(aCaption);

    aAllSettings.SetStyleSettings(aStyleSet);
    DefaultSettings = std::move(aAllSettings);
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
